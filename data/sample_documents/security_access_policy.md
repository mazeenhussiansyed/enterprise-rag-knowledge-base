# Information Security Access Policy

## Multi-Factor Authentication

Multi-factor authentication is mandatory for remote access, cloud applications, administrator consoles, and systems containing confidential or restricted data. Employees must use an approved authenticator application or hardware security key. SMS authentication is allowed only as a documented temporary recovery method approved by the service desk. Users must never approve an unexpected authentication request and must report repeated prompts to Security Operations immediately.

## Password and Credential Management

Passwords must contain at least fourteen characters and must not reuse any of the previous twelve passwords. Employees must store service-specific credentials in the approved password manager instead of browsers, spreadsheets, email, chat, or personal applications. Suspected credential exposure requires an immediate password reset and notification to Security Operations. Application secrets and service-account keys must be stored in the managed secrets platform and rotated according to their system risk classification.

## Privileged Access

Administrator access must use a separate named account and just-in-time elevation. An approved elevation window may not exceed eight hours. Shared administrator accounts are prohibited except for documented emergency accounts stored in the privileged access vault. Every privileged session is logged, and Information Security reviews the activity monthly. Administrators must not use privileged identities for email, web browsing, or ordinary productivity tasks.

## Remote Access

Connections to internal resources must use the company VPN from a managed device with current endpoint protection, operating-system patches, and disk encryption. Split tunneling is disabled for restricted environments. Employees must prevent family members or other unauthorized individuals from using company devices. A lost or stolen device must be reported to the service desk within one hour so that sessions can be revoked and remote-protection procedures can begin.

## Access Reviews and Removal

Managers and system owners must complete quarterly access certifications for confidential and restricted systems. Access that is no longer required must be removed within two business days. Reviews overdue by five business days are escalated to the responsible vice president. Human Resources termination events trigger immediate account disablement, while internal transfers require managers to review inherited permissions and request only the access needed for the new position.
