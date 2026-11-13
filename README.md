# DINGLI customer-facing machine availability portal

**Source**: Tencent Docs workbook `DWWxsb0ROcmtaUW5t`; worksheet `000002` (Saleable & Reserved Machines). Column headers supplied by the workbook owner, pending verification against row 1.

**Public output**: `docs/data.json` exposes **only** model, serial numbers, YOM, status, and ETA in Weert for one of the three allowed status values. Only publish fields the business approves for customers. Keep the original Tencent document restricted.

## Setup

1. Create a public GitHub repository. Upload the **contents** of this project folder at repository root, preserving `.github/workflows/sync.yml`. GitHub Pages is public and publicly exposes the generated `data.json`; publish only information approved for external disclosure. Do not make your original Tencent document public.
2. In repository Settings -> Pages -> Build and deployment -> Source, choose **GitHub Actions** (not Deploy from a branch). The scheduled workflow explicitly deploys the `docs/` directory.
3. Obtain Tencent Docs **OpenAPI OAuth** access for the account holding the sheet. Configure repository Settings -> Secrets and variables -> Actions -> **Secrets**: `TENCENT_ACCESS_TOKEN`, `TENCENT_CLIENT_ID`, `TENCENT_OPEN_ID`. Short-lived access tokens will expire; **automated refresh/renewal is not implemented**, so unattended operation requires another token lifecycle integration. Never post secrets in chat or commit credentials to GitHub.
4. Under Actions -> **Variables**, optionally set `TENCENT_SHEET_ID=000002`, `COL_MODEL=model`, `COL_SERIAL=serial numbers`, `COL_YOM=YOM`, `COL_STATUS=STOCK IN WEERT`, `COL_ETA=eta IN wEERT wAREHOUSE`. These are already defaults. Confirm `STOCK IN WEERT` contains the three status strings. The script expects headers in the first row of the API range.
5. Under Actions -> Update customer machine availability -> Run workflow, inspect the run and public `data.json`. The site will not publish if the read fails. Test that only three statuses and the five approved fields appear.
6. The workflow requests a refresh at minute 7/22/37/52 (UTC) each hour. Scheduled GitHub Actions can be delayed or skipped under load. The browser rereads the deployed snapshot each minute; a failure leaves the prior snapshot live, so monitor failures and the "Last synchronized" date. It is not real-time.

## Tencent API

The script uses the OpenAPI v2 spreadsheet range read path:
`GET https://docs.qq.com/openapi/spreadsheet/v2/files/{fileID}/sheets/{sheetID}/values?range=A1:AZ5000`
Headers: `Access-Token`, `Client-Id`, `Open-Id`. Confirm against your app's API entitlement and current Tencent documentation. Do not commit secrets or the original workbook.

## Important limitations

- The column names were provided by the owner but could not be verified from unauthenticated Tencent access. The header row must be the first row of the selected range. If not, adjust `TENCENT_RANGE`.
- `A1:AZ5000` caps the export at 5,000 rows; adjust range for larger files and paginate if required.
- Missing/renamed headers will fail safely; this avoids accidentally publishing unintended columns.
- If a machine is sold, its status becomes excluded on the next successful sync. The website still shows the last successful snapshot if sync fails; monitor workflow failures and show timestamp to users.
- If an API response uses a different cell data shape than expected, the adapter may require adjustment. Test against your authenticated account before launching.

## Source status mapping

Currently `STOCK IN WEERT` is assumed to contain `IN PRODUCTION`, `IN TRANSIT`, `YES - IN WEERT`. If these statuses are in another column, adjust `COL_STATUS`. Other values are excluded, not guessed from ETA. A blank YOM or ETA stays blank.
