import { config } from 'dotenv';
import path from 'path';

console.log("DOTENV_CONFIG_PATH:", process.env.DOTENV_CONFIG_PATH);
config({ path: process.env.DOTENV_CONFIG_PATH || '.env' });

console.log("WECOM_CORPID:", !!process.env.WECOM_CORPID);
console.log("FEISHU_APP_ID:", !!process.env.FEISHU_APP_ID);
