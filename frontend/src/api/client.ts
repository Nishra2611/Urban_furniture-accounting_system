import axios from 'axios'
export const API_URL=import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'
export const api=axios.create({baseURL:API_URL,headers:{'Content-Type':'application/json'}})
api.interceptors.request.use(c=>{const t=localStorage.getItem('uf_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c})
api.interceptors.response.use(r=>r,e=>{if(e.response?.status===401){localStorage.removeItem('uf_token');localStorage.removeItem('uf_user');if(location.pathname!='/login')location.href='/login'}return Promise.reject(e)})
export const err=(e:any)=>e?.response?.data?.detail || e?.message || 'Something went wrong'
