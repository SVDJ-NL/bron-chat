const envApiUrl = import.meta.env.PUBLIC_API_URL;
console.log('Environment API URL:', envApiUrl);

export const API_BASE_URL = envApiUrl || 'https://api.chat.bron.live';
console.log('Using API URL:', API_BASE_URL);