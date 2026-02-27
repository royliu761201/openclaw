import axios from 'axios';
const tenantResp = await axios.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', {
  app_id: 'cli_a91a394c76389cee',
  app_secret: 'r21wWNXdVQLIbueoAYgFrhTZItOWtZ1b'
});
const token = tenantResp.data.tenant_access_token;
console.log('Got Tenant Token:', token);

try {
  const infoResp = await axios.get('https://open.feishu.cn/open-apis/bot/v3/info', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log('Bot Info Success:', infoResp.data);
} catch (err) {
  if (err.response) {
    console.error('Feishu API Error:', JSON.stringify(err.response.data, null, 2));
  } else {
    console.error('Network Error:', err.message);
  }
}
