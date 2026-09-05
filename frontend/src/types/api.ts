export type Role='User'|'Accountant'|'Administrator'|'user'|'accountant'|'admin'
export type Status='draft'|'confirmed'|'posted'|'cancelled'|'partial'|'paid'|'overdue'|'Draft'|'Confirmed'|'Posted'|'Cancelled'
export interface User{ id:number|string; name:string; login_id:string; email:string; role:Role|string; is_active:boolean }
export interface TokenResponse{access_token:string;token_type:string;user?:User}
export interface Contact{ id:number|string;name:string;code?:string;party_type?:string;contact_type?:string;email?:string|null;phone?:string|null;address?:string|null;tax_id?:string|null;is_active:boolean }
export interface Product{ id:number|string;name:string;code?:string;sku?:string;description?:string|null;sales_price?:number|string;unit_price?:number|string;purchase_price?:number|string;cost_price?:number|string;tax_rate?:number|string;tax_id?:string|null;income_account_id?:number|string|null;expense_account_id?:number|string|null;is_active:boolean }
export interface Tax{ id:number|string;name:string;rate:number|string;tax_type:string;is_active:boolean }
export interface Account{ id:number|string;code:string;name:string;account_type:string;parent_id?:number|string|null;is_active:boolean }
export interface Journal{ id:number|string;code:string;name:string;journal_type:string;is_active:boolean }
export interface Analytic{ id:number|string;code:string;name:string;is_active:boolean }
export interface Budget{ id:number|string;name:string;account_id:number|string;start_date:string;end_date:string;amount:number|string;committed?:number|string;achieved?:number|string }
export interface Line{product_id:number|string;description?:string;quantity:number;unit_price?:number;tax_rate?:number}
export interface Document{ id:number|string;number:string;customer_id?:number|string;vendor_id?:number|string;contact_id?:number|string;invoice_date?:string;bill_date?:string;order_date?:string;due_date?:string|null;status:string;total:number|string;amount_paid?:number|string }
export interface Payment{ id:number|string;number:string;payment_date:string;payment_type:string;contact_id:number|string;invoice_id?:number|string|null;bill_id?:number|string|null;amount:number|string;method:string;reference?:string|null }
export interface Dashboard{sales_orders:number;purchase_orders:number;invoices:number;bills:number;payments:number;receivables_due:number|string;payables_due:number|string}
