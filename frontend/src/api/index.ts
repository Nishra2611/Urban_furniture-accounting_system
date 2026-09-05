import {api} from './client'
export const auth={login:(d:any)=>api.post('/auth/login',d),signup:(d:any)=>api.post('/auth/signup',d),logout:()=>api.post('/auth/logout'),me:()=>api.get('/users/me'),forgot:(email:string)=>api.post('/auth/forgot-password',null,{params:{email}}),reset:(d:any)=>api.post('/auth/reset-password',d),change:(d:any)=>api.post('/auth/change-password',d)}
export const users={list:()=>api.get('/users'),create:(d:any)=>api.post('/users',d),update:(id:string,d:any)=>api.patch(`/users/${id}`,d)}
export const masters={
 contacts:{list:()=>api.get('/contacts'),create:(d:any)=>api.post('/contacts',d),update:(id:string,d:any)=>api.patch(`/contacts/${id}`,d),deactivate:(id:string)=>api.delete(`/contacts/${id}`)},
 products:{list:()=>api.get('/products'),create:(d:any)=>api.post('/products',d),update:(id:string,d:any)=>api.patch(`/products/${id}`,d),deactivate:(id:string)=>api.delete(`/products/${id}`)},
 taxes:{list:()=>api.get('/taxes'),create:(d:any)=>api.post('/taxes',d),deactivate:(id:string)=>api.delete(`/taxes/${id}`)},
 accounts:{list:()=>api.get('/accounts'),create:(d:any)=>api.post('/accounts',d),deactivate:(id:string)=>api.delete(`/accounts/${id}`)},
 journals:{list:()=>api.get('/journals'),create:(d:any)=>api.post('/journals',d),deactivate:(id:string)=>api.delete(`/journals/${id}`)},
 analytics:{list:()=>api.get('/analytic-accounts'),create:(d:any)=>api.post('/analytic-accounts',d)},
 budgets:{list:()=>api.get('/budgets'),create:(d:any)=>api.post('/budgets',d)}
}
export const tx={
 salesOrders:{list:()=>api.get('/sales-orders'),create:(d:any)=>api.post('/sales-orders',d),confirm:(id:string)=>api.post(`/sales-orders/${id}/confirm`)},
 purchaseOrders:{list:()=>api.get('/purchase-orders'),create:(d:any)=>api.post('/purchase-orders',d),confirm:(id:string)=>api.post(`/purchase-orders/${id}/confirm`)},
 invoices:{list:()=>api.get('/invoices'),get:(id:string)=>api.get(`/invoices/${id}`),create:(d:any)=>api.post('/invoices',d),post:(id:string)=>api.post(`/invoices/${id}/post`),cancel:(id:string)=>api.post(`/invoices/${id}/cancel`)},
 bills:{list:()=>api.get('/bills'),get:(id:string)=>api.get(`/bills/${id}`),create:(d:any)=>api.post('/bills',d),post:(id:string)=>api.post(`/bills/${id}/post`),cancel:(id:string)=>api.post(`/bills/${id}/cancel`)},
 payments:{list:()=>api.get('/payments'),create:(d:any)=>api.post('/payments',d)}
}
export const accounting={entries:{list:()=>api.get('/journal-entries'),create:(d:any)=>api.post('/journal-entries',d)}}
export const reports={pl:(p:any)=>api.get('/reports/profit-loss',{params:p}),bs:(p:any)=>api.get('/reports/balance-sheet',{params:p}),gl:(p:any)=>api.get('/reports/general-ledger',{params:p}),budget:()=>api.get('/reports/budget')}
export const dashboard=()=>api.get('/dashboard')
