# Screenshot-derived implementation notes

The UI follows the supplied wireframes as an accounting workspace rather than copying their sketch styling literally:
- Login and signup are centered, form-first screens with the App Logo/Urban Furniture identity and Forgot Password / Sign Up navigation.
- Create User includes Name, Login Id, Email Id, Role, Password and Re-enter Password. Roles are User, Accountant and Administrator.
- The authenticated workspace uses the Sales / Purchase / Account / Report mental model through a grouped sidebar.
- Master modules default to List view and also provide Kanban cards, Search, New, saved-record form navigation, Back and Archive where the backend supports deactivation.
- Contact form keeps the screenshot's business-contact concept while using the backend's current fields, including Contact Type.
- Product form uses the backend's current Product fields instead of displaying unsupported mock-only Category/Image/Product Type fields.
- Journal Entry includes Accounting Date, Journal, Account, Partner, Debit and Credit, with client-side debit=credit validation before submit.
- Budget report exposes Budget, Committed, Achieved, Remaining and Variance from the live report endpoint.
- Purchase and sales flows use master selections and document status actions, with payment screens for Receive/Send and Cash/Bank/Card.
- User role is restricted to the portal experience for their own backend-scoped invoices, bills and payments.
