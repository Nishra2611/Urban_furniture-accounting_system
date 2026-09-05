import {createContext,useContext,useEffect,useState,type ReactNode} from 'react'
import {auth} from '../api'
import type {User} from '../types/api'
type Ctx={user:User|null;loading:boolean;login:(d:any)=>Promise<void>;signup:(d:any)=>Promise<void>;logout:()=>Promise<void>}
const Auth=createContext<Ctx>(null as any)
export function AuthProvider({children}:{children:ReactNode}){const [user,setUser]=useState<User|null>(()=>{try{return JSON.parse(localStorage.getItem('uf_user')||'null')}catch{return null}});const [loading,setLoading]=useState(true)
 useEffect(()=>{if(localStorage.getItem('uf_token'))auth.me().then(r=>{setUser(r.data);localStorage.setItem('uf_user',JSON.stringify(r.data))}).catch(()=>{}).finally(()=>setLoading(false));else setLoading(false)},[])
 const login=async(d:any)=>{const r=await auth.login(d);localStorage.setItem('uf_token',r.data.access_token);const me=await auth.me();localStorage.setItem('uf_user',JSON.stringify(me.data));setUser(me.data)}
 const signup=async(d:any)=>{const payload={login_id:d.login_id,email:d.email,password:d.password,re_password:d.re_password||d.re_enter_password};await auth.signup(payload);await login({login_id:d.login_id,password:d.password})}
 const logout=async()=>{try{await auth.logout()}catch{}localStorage.removeItem('uf_token');localStorage.removeItem('uf_user');setUser(null)}
 return <Auth.Provider value={{user,loading,login,signup,logout}}>{children}</Auth.Provider>}
export const useAuth=()=>useContext(Auth)
