
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
import gc
from transformers import (
    TrainerCallback,
    TrainingArguments,
)
from transformers.trainer_pt_utils import get_parameter_names
from trl import SFTTrainer

from .config import CONFIG, GlobalConfig
from .evaluator import MedTimeCallback

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# 0. Callbacks
# -----------------------------------------------------------------------------


class StagedTrainingCallback(TrainerCallback):
    """
    Curriculum Learning Callback.
    Phase 1 (Warmup): SFT Loss Only (All logic-related lambdas = 0)
    Phase 2 (Alignment): SFT + Multi-component Logic Loss (Restore target lambdas)
    """
    def __init__(self, trainer, warmup_epochs, logic_config: dict):
        self.trainer = trainer
        self.warmup_epochs = warmup_epochs
        self.logic_config = logic_config  # e.g., {"lambda_logic": 1.0, "lambda_grounding": 0.5, "lambda_order": 0.1}

    def on_epoch_begin(self, args, state, control, **kwargs):
        current_epoch = state.epoch
        is_warmup = current_epoch < self.warmup_epochs
        
        for attr_name, target_value in self.logic_config.items():
            value = 0.0 if is_warmup else target_value
            setattr(self.trainer, attr_name, value)
            
        phase_name = "Warmup (Logic Disabled)" if is_warmup else "Alignment (Logic Enabled)"
        weights_str = ", ".join([f"{k}={getattr(self.trainer, k)}" for k in self.logic_config.keys()])
        logger.info(f"🎓 [Curriculum] Epoch {current_epoch:.1f}: {phase_name} | {weights_str}")


# -----------------------------------------------------------------------------
# 1. MedTime Logic Head
# -----------------------------------------------------------------------------
class MedTimeLogicHead(nn.Module):
    """Logic Head for Topological Consistency"""
    def __init__(self, hidden_size, max_drift_days=365, force_verifier_on=False):
        super().__init__()
        self.max_drift = max_drift_days
        self.force_verifier_on = force_verifier_on
        self.projector = nn.Linear(hidden_size, 1)
        self.verifier = nn.Sequential(
            nn.Linear(hidden_size * 2, 512), 
            nn.LayerNorm(512),
            nn.ReLU(), 
            nn.Linear(512, 1), 
            nn.Sigmoid()
        )

    def forward(self, h_e, h_t):
        n = h_e.size(0)
        taus = self.projector(h_t).squeeze(-1)
        if n < 2:
            return taus, torch.tensor(0.0, device=h_e.device, requires_grad=True), 0.0

        hi = h_e.repeat_interleave(n, dim=0)
        hj = h_e.repeat(n, 1)
        if getattr(self, "force_verifier_on", False):
            w_ij = torch.ones(n, n, device=h_e.device)
        else:
            w_ij = self.verifier(torch.cat([hi, hj], dim=-1)).view(n, n)

        diff_matrix = taus.unsqueeze(1) - taus.unsqueeze(0)
        mask = torch.triu(torch.ones(n, n), diagonal=1).to(h_e.device)
        violation_matrix = F.softplus(diff_matrix + 0.1)

        loss_topo = (violation_matrix * w_ij * mask).sum() / (mask.sum() + 1e-6)
        drift_penalty = F.relu(torch.abs(diff_matrix) - self.max_drift) * mask
        loss_drift = (drift_penalty * w_ij).sum() / (mask.sum() + 1e-6)

        loss_topo = loss_topo + 0.1 * loss_drift
        with torch.no_grad():
            v_count = ((diff_matrix > 0) * mask).sum()
            latent_vr = v_count / (mask.sum() + 1e-6)

        return taus, loss_topo, latent_vr.item()


# -----------------------------------------------------------------------------
# 2. MedTime Trainer
# -----------------------------------------------------------------------------
class MedTimeTrainer(SFTTrainer):
    def __init__(self, *args, alpha_cons=0.5, lambda_logic=0.2, beta_ground=0.1, **kwargs):
        super().__init__(*args, **kwargs)
        self.alpha_cons = alpha_cons
        self.lambda_logic = lambda_logic
        self.beta_ground = beta_ground

        self.logic_head = MedTimeLogicHead(
            self.model.config.hidden_size, 
            max_drift_days=CONFIG.max_drift_days,
            force_verifier_on=kwargs.get("force_verifier_on", False)
        ).to(self.model.device)
        tk = getattr(self, "processing_class", self.tokenizer)
        self.trig_patterns = self._detect_patterns(tk, "trigger")
        self.t_patterns = self._detect_patterns(tk, "t")

    def _load_logic_head(self, checkpoint_path):
        """Helper to load logic_head from a specific checkpoint"""
        logic_head_path = os.path.join(checkpoint_path, "logic_head.bin")
        if os.path.exists(logic_head_path):
            try:
                self.logic_head.load_state_dict(
                    torch.load(logic_head_path, map_location=self.model.device, weights_only=True)
                )
                logger.info(f"🔄 LogicHead restored from checkpoint: {logic_head_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load LogicHead due to architecture mismatch: {e}")
                logger.info("🆕 Initializing new LogicHead.")

    def save_model(self, output_dir=None, _internal_call=False):
        super().save_model(output_dir, _internal_call)
        
        # [FIX] DDP Race Condition: Only rank 0 should save the custom logic head
        if self.is_world_process_zero():
            if output_dir is None:
                output_dir = self.args.output_dir
            
            os.makedirs(output_dir, exist_ok=True)
            logic_head_path = os.path.join(output_dir, "logic_head.bin")
            torch.save(self.logic_head.state_dict(), logic_head_path)
            logger.info(f"💾 LogicHead saved to: {logic_head_path}")

    def create_optimizer(self):
        if self.optimizer is None:
            decay_parameters = get_parameter_names(self.model, [nn.LayerNorm])
            decay_parameters = [n for n in decay_parameters if "bias" not in n]
            optimizer_grouped_parameters = [
                {
                    "params": [
                        p
                        for n, p in self.model.named_parameters()
                        if (n in decay_parameters and p.requires_grad)
                    ],
                    "weight_decay": self.args.weight_decay,
                },
                {
                    "params": [
                        p
                        for n, p in self.model.named_parameters()
                        if (n not in decay_parameters and p.requires_grad)
                    ],
                    "weight_decay": 0.0,
                },
                {
                    "params": [p for p in self.logic_head.parameters() if p.requires_grad],
                    "weight_decay": self.args.weight_decay,
                    "lr": self.args.learning_rate,
                },
            ]

            optimizer_cls, optimizer_kwargs = self.get_optimizer_cls_and_kwargs(self.args)
            self.optimizer = optimizer_cls(optimizer_grouped_parameters, **optimizer_kwargs)

        return self.optimizer

    @staticmethod
    def _detect_patterns(tokenizer, char):
        variants = [
            f'"{char}":', f' "{char}":', f'"{char}": ', f' "{char}": ',
            f'{{"{char}":', f',"{char}":', f'"{char}":"', f'"{char}": "',
            f',"{char}":"', f',"{char}": "',
        ]
        patterns = []
        for v in variants:
            ids = tokenizer.encode(v, add_special_tokens=False)
            if ids:
                patterns.append(ids)
        
        patterns.append(tokenizer.encode(char, add_special_tokens=False))
        patterns.append(tokenizer.encode('":"', add_special_tokens=False))
            
        return patterns

    def _find_indices(self, token_ids_tensor, patterns):
        idx = []
        for p in patterns:
            pt = torch.tensor(p).to(token_ids_tensor.device)
            if len(token_ids_tensor) < len(pt):
                continue
            matches = (token_ids_tensor.unfold(0, len(pt), 1) == pt).all(dim=1)
            idx.extend((matches.nonzero(as_tuple=True)[0] + len(pt)).tolist())
        return sorted(list(set(idx)))

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        is_train = model.training
        outputs = model(**inputs, output_hidden_states=True)
        lm_loss = outputs.loss

        h_states = outputs.hidden_states[-1]
        
        if hasattr(self, "logic_head") and self.logic_head is not None:
            self.logic_head.to(h_states.device)
            
        input_ids = inputs["input_ids"]
        labels = inputs.get("labels")
        token_ranges_batch = inputs.get("token_ranges")

        mse_sum = torch.tensor(0.0, device=lm_loss.device)
        topo_sum = torch.tensor(0.0, device=lm_loss.device)
        ground_sum = torch.tensor(0.0, device=lm_loss.device)
        vr_sum = 0.0
        s_count, p_count = 0, 0

        for b in range(input_ids.size(0)):
            non_masked = (labels[b] != -100).nonzero(as_tuple=True)[0]
            if len(non_masked) == 0:
                continue
            res_start = non_masked[0].item()

            trig_gen_idx = [
                i for i in self._find_indices(input_ids[b], self.trig_patterns) if i >= res_start
            ]
            t_gen_idx = [
                i for i in self._find_indices(input_ids[b], self.t_patterns) if i >= res_start
            ]

            current_sample_ranges = (
                token_ranges_batch[b]
                if (token_ranges_batch and b < len(token_ranges_batch))
                else []
            )
            h_trigs, h_ts = [], []

            num_nodes = min(len(trig_gen_idx), len(t_gen_idx))
            for i in range(num_nodes):
                ti, tt = trig_gen_idx[i], t_gen_idx[i]
                if ti < h_states.size(1) and tt < h_states.size(1):
                    v_trig = h_states[b, ti]
                    v_time = h_states[b, tt]
                    h_trigs.append(v_trig)
                    h_ts.append(v_time)

                    mse_sum += F.mse_loss(v_trig, v_time)

                    if i < len(current_sample_ranges):
                        node_source_indices = current_sample_ranges[i]
                        if node_source_indices:
                            idx_tensor = torch.tensor(
                                node_source_indices, device=h_states.device, dtype=torch.long
                            )
                            v_source = torch.index_select(h_states[b], 0, idx_tensor).mean(dim=0)
                            ground_sum += F.mse_loss(v_trig, v_source)

                    p_count += 1

            if len(h_trigs) >= 2:
                _, l_topo, l_vr = self.logic_head(torch.stack(h_trigs), torch.stack(h_ts))
                topo_sum += l_topo
                vr_sum += l_vr
                s_count += 1

        norm_mse = mse_sum / (p_count + 1e-6)
        norm_topo = topo_sum / (s_count + 1e-6)
        norm_ground = ground_sum / (p_count + 1e-6)

        total_loss = (
            lm_loss
            + (self.alpha_cons * norm_mse)
            + (self.lambda_logic * norm_topo)
            + (self.beta_ground * norm_ground)
        )

        should_log = is_train and (self.state.global_step % 10 == 0)

        if should_log:
            self.log(
                {
                    "lm_loss": round(lm_loss.item(), 4),
                    "mse_loss": round(norm_mse.item(), 4),
                    "ground_loss": round(norm_ground.item(), 4),
                    "topo_loss": round(norm_topo.item(), 4),
                    "latent_vr": round(vr_sum / (s_count + 1e-6), 4),
                }
            )

        del inputs
        if not is_train:
            total_loss = total_loss.detach()
        return (total_loss, outputs) if return_outputs else total_loss


def init_medtime_trainer(model, tokenizer, train_ds, eval_ds, custom_collator, run_name, output_dir, cfg):
    """Initializes MedTimeTrainer with hardware-optimal configuration."""
    optim_type = "adamw_8bit"
    use_fp16 = False
    use_bf16 = False
    
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        logger.info(f"🚀 Configuring Trainer for Hardware: {gpu_name}")
        # L20, A100, H100 etc. support BF16
        if any(x in gpu_name for x in ["L20", "A100", "H100", "A10G", "L40"]):
            use_bf16 = True
            logger.info("✨ BF16 Enabled for high-precision training.")
        elif "T4" in gpu_name or "P100" in gpu_name:
            use_fp16 = True
            optim_type = "paged_adamw_8bit" if "T4" in gpu_name else "adamw_8bit"

    save_steps = cfg.get("save_steps", cfg.get("eval_steps", 2))
    if GlobalConfig.TRAIN_PARAMS.get("save_steps_override") is not None:
        save_steps = GlobalConfig.TRAIN_PARAMS["save_steps_override"]

    t_args = TrainingArguments(
        run_name=run_name,
        output_dir=output_dir,
        remove_unused_columns=False,
        per_device_train_batch_size=cfg.get("batch_size", CONFIG.batch_size),
        gradient_accumulation_steps=cfg.get("grad_accum", CONFIG.grad_accumulation),
        learning_rate=cfg.get("learning_rate", CONFIG.learning_rate),
        optim=optim_type,
        max_steps=cfg.get("max_steps", GlobalConfig.TRAIN_PARAMS["max_steps"]),
        fp16=use_fp16,
        bf16=use_bf16,
        tf32=True,
        dataloader_num_workers=4,
        dataloader_pin_memory=True,
        warmup_ratio=0.1,
        logging_steps=cfg.get("logging_steps", 1),
        eval_strategy="steps" if eval_ds else "no",
        eval_steps=cfg.get("eval_steps", 2),
        save_strategy="steps" if eval_ds else "no",
        save_steps=save_steps,
        save_total_limit=cfg.get("save_total_limit", 3),
        per_device_eval_batch_size=1,
        eval_accumulation_steps=1,
        prediction_loss_only=True,
        load_best_model_at_end=True if eval_ds else False,
        metric_for_best_model="eval_loss" if eval_ds else None,
        gradient_checkpointing=True,
        report_to="wandb" if CONFIG.use_wandb else "none",
    )
    
    # [FIX] TRL / Transformers Compatibility
    # Older TRL versions expect 'push_to_hub_token' in TrainingArguments and try to pop it.
    # Modern Transformers removed it. We inject it to allow the pop() to succeed without error.
    # [FIX] TRL / Transformers Compatibility
    # Older TRL versions expect 'push_to_hub_token' in TrainingArguments and try to pop it.
    # Modern Transformers removed it. We force-inject it into __dict__ to comply.
    if "push_to_hub_token" not in t_args.__dict__:
        t_args.__dict__["push_to_hub_token"] = None

    # Initial Lambda setup
    init_lambda = cfg.get("lambda_logic", 0.1)
    is_staged = cfg.get("staged_training", CONFIG.staged_training)
    
    if is_staged:
        logger.info(f"🏫 Staged Training Enabled. Initializing lambda_logic to 0.0")
        init_lambda = 0.0 # Force 0 start
        
    trainer_kwargs = {
        "model": model,
        "processing_class": tokenizer,
        "train_dataset": train_ds,
        "eval_dataset": eval_ds,
        "args": t_args,
        "data_collator": custom_collator,
        "alpha_cons": cfg.get("alpha_cons", 0.3) if cfg["family"] == "llm_medtime" else 0.0,
        "lambda_logic": init_lambda if cfg["family"] == "llm_medtime" else 0.0,
        "beta_ground": cfg.get("beta_ground", 0.2) if cfg["family"] == "llm_medtime" else 0.0,
    }
    
    trainer = MedTimeTrainer(**trainer_kwargs)

    if is_staged and cfg["family"] == "llm_medtime":
        warmup = cfg.get("warmup_epochs", CONFIG.warmup_epochs)
        
        logic_config = {
            "lambda_logic": cfg.get("final_lambda", CONFIG.final_lambda),
            "alpha_cons": cfg.get("alpha_cons", 0.3),
            "beta_ground": cfg.get("beta_ground", 0.2),
        }
        
        trainer.add_callback(StagedTrainingCallback(trainer, warmup, logic_config))
        logger.info(f"🏫 Registered StagedTrainingCallback (Warmup={warmup}ep, Config={logic_config})")

    return trainer
