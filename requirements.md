# Termination Liability Engine — Requirements Document

**Author:** Sanjana  
**Date:** 2026-04-17  
**Status:** Draft  

---

## 1. Problem Statement

Rippling holds deposits from EOR customers to cover the cost of terminating an employee. Deposits are expected to cover some, but typically not all, of the ultimate costs to terminate an EOR EE without cause (ie. redundancy). But the model used to estimate that cost does not provide an accurate representation under certain circumstances. This leads to Rippling taking on much more financial risk than we estimate and our deposits covering a smaller portion of this risk.

**Wrong salary base** - the calculation uses "monthly salary" as provided to Risk without any country-specific modifications. Many countries require notice period, and in some cases severance pay, to include total compensation - base + allowances + commissions. So our calculations for severance pay as well as PILON are inaccurate as we're using the wrong base.

**Country specific severance logic** - the country level rules are currently hardcoded in Risk Platform which is static and doesn't adapt with changing regulations. The current rules also cannot factor in province-level or employment model (e.g. consultant vs. staff aug) nuances within a given country.

**Mutual separation agreement** - in certain countries, Rippling's standard termination practice is to obtain a mutual separation agreement from the employee - This occurs where statutory notice/severance requirements are unclear, or where legal risks are high. These agreements require an additional payment on top of or in place of statutory amounts — ranging from ~1 week to 6 months of standard pay — to get the employee's signature. Currently, there is no country-level configuration capturing where this practice applies, so the additional liability is invisible to the deposit calculation and results in under-collateralization in these markets.

---

## 2. Compensation Variable Metadata

For every compensation variable in the system, we need to collect the following per-country metadata:


| Field                        | Type   | Description                                                   |
| ---------------------------- | ------ | ------------------------------------------------------------- |
| `included_in_working_notice` | `bool` | Is this comp variable paid during working notice period?      |
| `included_in_severance`      | `bool` | Is this comp variable included in the severance salary basis? |


### Example: Philippines (PH)


| Compensation Variable            | Included in Working Notice Gross Pay? | Included in Severance Basis? |
| -------------------------------- | ------------------------------------- | ---------------------------- |
| Gross base salary                | Yes                                   | Yes                          |
| Target bonus                     | Yes                                   | No                           |
| Signing bonus                    | Yes                                   | No                           |
| On-target commission             | Yes                                   | No                           |
| Rice allowance                   | Yes                                   | No                           |
| Uniform and clothing allowance   | Yes                                   | No                           |
| Laundry allowance                | Yes                                   | No                           |
| Medical cash allowance           | Yes                                   | No                           |
| Internet allowance               | Yes                                   | No                           |
| Medical assistance allowance     | Yes                                   | No                           |
| Productivity incentive allowance | Yes                                   | No                           |
| Christmas or anniversary gift    | Yes                                   | No                           |
| 13th month salary                | Yes                                   | No                           |


In the Philippines, all compensation variables are paid during working notice (full gross pay continues). But for severance calculation purposes, only gross base salary is included — allowances, bonuses, and commissions are excluded from the severance basis.

This table needs to be collected for every EOR country. It drives which `salary_basis` Risk needs to use to calculate severance amount and salary during notice period.

### Where this lives

This metadata is per-country, per compensation variable. We need to provide an interface for admins (either through Control Center or through Retool) to:

1. View the list of compensation variables for a country
2. See whether each variable is mandatory or optional
3. Update Yes/No for `included_in_working_notice` and `included_in_severance`

Every time a new compensation variable is created for a country, this metadata needs to be collected. Both fields default to **No** for new variables.

---

## 3. Termination Liability Rules — Admin Interface

We need to allow HR admins to input termination cost rules per country. The Control Center UI is P1 — if Retool is easier to ship first, start there and migrate to Control Center later.

### 3.1 General Inputs

Collect the following from the HR admin when setting up a country:

| Input | Options | Description |
|---|---|---|
| Country | Country code selector (e.g., `PH`, `IN`, `GB`) | Which country this configuration applies to |
| What is the contract type? | `Fixed Term` / `Indefinite` | Determines which type of contract model this applies to |
| Is a mutual termination agreement (MTA) the default practice? | `Yes` / `No` | Whether Rippling typically negotiates a separation agreement in this country |

If MTA default = **Yes**, additionally collect:

**How many days does it take to secure the MTA, on average?**

Admin enters a fixed number of days (e.g., `30` days).

**How many days of severance are offered in exchange for the MTA signature?**

Select calculation type: `Fixed` / `Per year of service` / `Tenure-based`

- **If Fixed:** Admin enters a number (e.g., `90` days)
- **If Per year of service:** Admin enters days per year (e.g., `15` days/year) + Prorate partial years? `Yes` / `No`
- **If Tenure-based:** Admin enters tiers as explicit ranges:

  | From | To | Days |
  |---|---|---|
  | 0 months | 24 months | x days |
  | 24 months | 48 months | y days |
  | 48 months | ∞ | z days |

  The admin can click **[ + Add tier ]** to add additional brackets.

### 3.2 Severance Cost Components

The admin can define one or more termination cost components per country. "Redundancy Pay" is included by default.

**For each cost component:**

**Step 1 — Select the calculation type:** `Fixed` / `Per year of service` / `Tenure-based`

**If Fixed:**
- How many days of severance are offered? → Admin enters a number (e.g., `90` days)

**If Per year of service:**
- How many days of severance per year of service? → Admin enters a number (e.g., `30` days)
- Prorate partial years? → `Yes` / `No` (e.g., 2.5 years at 30 days/year = 75 days if Yes, 60 days if No)

**If Tenure-based:**
- Admin enters tiers as explicit ranges:

| From | To | Days of severance |
|---|---|---|
| 0 months | 24 months | x days |
| 24 months | 48 months | y days |
| 48 months | ∞ | z days |

The admin can click **[ + Add tier ]** to add additional brackets.

**To add another cost component** (e.g., "Gratuity", "Seniority Premium"), the admin clicks **[ + Add component ]** and provides:
- A label for the component (e.g., "Gratuity")
- The same Fixed / Per year of service / Tenure-based selection as above

### 3.3 Vacation Payout

| Input | Options | Description |
|---|---|---|
| Do you pay out accrued vacation during termination? | `Yes` / `No` | Whether unused leave is paid at termination |

If vacation payout = **Yes**, additionally collect:

| Input | Options | Description |
|---|---|---|
| What is the minimum that needs to be paid out? | `All Accrued` / Fixed number of days | `All Accrued` = full balance; otherwise admin enters a number |

### 3.4 Eligibility — Condition Block

Each termination liability config needs a condition block that determines **which employees this rule applies to**. This is critical because a single country can have multiple termination configs — e.g., different rules for different contract types, employment models, or provinces.

The condition block uses the same condition builder pattern available in Compliance 360 today. It consists of:

**Include criteria** — defines the population this rule covers:

| Attribute | Description | Example values |
|---|---|---|
| Is an EOR Employee? | Whether the employee is employed through Rippling EOR | True / False |
| Country | The employee's work country | PH, AU, GB, IN |
| Contract Type | The type of employment contract | Indefinite, Fixed Term |
| Employment Model | How the employee is engaged | Staff Augmentation, Consultant, Direct Hire |
| Province / State | Sub-national region (where rules vary by region) | Ontario, Queensland, Bavaria |
| Worker Category | The classification of the worker | Full-Time, Part-Time |

**Exclude criteria** — carves out populations that should NOT be covered by this rule:

| Attribute | Description | Example values |
|---|---|---|
| Worker Type | Excludes specific worker types | Contractors, Interns |
| Specific Groups | Named groups to exclude | All - Contractors, All - Temps |

#### How it works

The admin builds conditions using AND/OR logic:

1. **Include people who are** — one or more conditions that must all be true (AND logic)
2. **Except** — one or more groups to exclude from the included population

#### Example: Philippines EOR employees

> **Include people who are:**
>
> Employee → Is an EOR Employee? is `True`
> AND Country is `PH`
> AND Contract Type is `Indefinite`
>
> **Except:** All - Contractors

This rule would apply to all EOR employees in the Philippines on indefinite contracts, excluding anyone classified as a contractor.

#### Example: Australia — different rules by tenure threshold

A country could have two configs with different condition blocks:

**Config 1 — Standard redundancy (most employees):**
> **Include:** EOR Employee = True AND Country = AU AND Contract Type = Indefinite
> **Except:** All - Contractors

**Config 2 — Fixed term contracts:**
> **Include:** EOR Employee = True AND Country = AU AND Contract Type = Fixed Term

#### Rule resolution

When multiple configs exist for a country, the system evaluates them in the order the admin has arranged them. The **first matching rule wins**. If no rule matches, the employee is flagged for manual review — there is no silent fallback to avoid under-collateralization.

Admins can reorder rules by dragging them in the UI, so more specific rules (e.g., province-specific) should be placed above broader rules (e.g., country-wide).

### 3.5 Example: Philippines

Here's what the admin would fill out for the Philippines:

**General Inputs:**

| Input | Value |
|---|---|
| What is the contract type? | `Indefinite` |
| Is MTA the default practice? | `No` |

**Cost Component 1: Redundancy Pay** (default)

| Field | Value |
|---|---|
| Calculation type | `Per year of service` |
| Days per year of service | 30 days |
| Prorate partial years? | Yes |

**Vacation Payout:**

| Input | Value |
|---|---|
| Pay out accrued vacation during termination? | `Yes` |
| Minimum payout | `All Accrued` |

**Eligibility:**

> **Include people who are**
>
> Employee → Is an EOR Employee? is True
>
> **Except:** All - Contractors

### 3.6 Storage and Retrieval

These admin input values should be stored as a configuration for each country (potentially GeoConfig). We also need to provide a way to retrieve this configuration for a given country which admins can modify if needed.

---

## 4. Runtime Calculation

### 4.1 What to calculate during hiring/transition

During hiring or role transition, we should calculate the following for each role and pass it to the risk role bean:

**`severance_days`** — The number of days we owe severance for.

**If MTA is not the default:**
- Fetch the tenure in days for the employee
- Iterate through all severance cost components in the country config
- Evaluate each component against the employee's tenure and conditions
- Sum the results → this is `severance_days`

**If MTA is the default:**
- Evaluate the MTA severance config (which can be Fixed / Per year of service / Tenure-based, just like regular severance components) against the employee's tenure → this is `severance_days`
- Additionally pass `mta_days` — the fixed number of days it takes to secure the MTA on average (from config)

**`vacation_days_payout`** — If the country config specifies "All Accrued", pass the employee's accrued vacation days. Otherwise, pass `min(accrued vacation days, statutory minimum from config)`. For example: if an employee has 30 days accrued but the statutory minimum payout is 5 days, we pass 5. If an employee has only 2 days accrued, we pass 2.

### 4.2 Compensation information

To calculate the dollar amount of severance and notice period pay, Risk needs to know the full compensation breakdown — not just a single "monthly salary" number. We need to modify the compensation object passed to Risk to include:

| Field | Description | Example values |
|---|---|---|
| Compensation Key | The compensation variable identifier | `base_salary`, `housing_allowance`, `commission` |
| Unit | How the compensation is earned/measured | `Monthly`, `Annually`, `Quarterly`, `One Time` |
| Payout Frequency | How often the compensation is paid out | `Monthly`, `One Time`, `Quarterly` |

This allows Risk to determine, for each compensation variable, whether it is included in the severance basis or notice period pay (using the metadata from Section 2), and to correctly annualize or prorate amounts based on unit and payout frequency.

**Handling bonus rate vs bonus amount:** Some compensation variables are defined as a percentage of base salary (e.g., 10% annual bonus) rather than a fixed amount. We should always resolve percentages to amounts before passing them into the compensation array. The compensation array is assembled at hiring/transition time when the base salary is known, so the conversion is straightforward. This keeps Risk's job simple — it only reads amounts, never needs to resolve percentages.

### 4.3 Current vs New Risk Role Bean

**Current JSON passed to Risk:**

```json
{
  "roleId": "abc123",
  "roleTransitionId": null,
  "companyEntityRelationshipId": "cer456",
  "country": "PH",

  "yearlySalary": { "value": 1200000, "currency_type": "PHP" },
  "targetAnnualBonus": null,
  "targetAnnualBonusPercent": 0,
  "onTargetCommission": null,

  "isTotalVacationDaysMissing": false,
  "totalVacationDays": 15,
  "defaultVacationDays": 5,
  "statutoryVacationDays": 5,

  "isNoticePeriodMissing": false,
  "noticePeriodType": "STANDARD",
  "noticePeriodInDays": 30,
  "statutoryNoticePeriodInDays": 30,

  "isProbationPeriodMissing": false,
  "probationPeriodQuantity": 6,
  "probationPeriodUnit": "MONTHS",
  "probationPeriodEndDate": "2026-10-17",
  "defaultProbationPeriodQuantity": 6,
  "defaultProbationPeriodUnit": "MONTHS",
  "defaultProbationPeriodEndDate": "2026-10-17",

  "tenureInDays": 0,
  "countryJobFields": null
}
```

**Proposed new JSON passed to Risk:**

```json
{
  "roleId": "abc123",
  "roleTransitionId": null,
  "companyEntityRelationshipId": "cer456",
  "country": "PH",

  "compensation": [
    { "key": "base_salary", "value": 100000, "currency": "PHP", "unit": "Monthly", "payout_frequency": "Monthly" },
    { "key": "rice_allowance", "value": 2000, "currency": "PHP", "unit": "Monthly", "payout_frequency": "Monthly" },
    { "key": "internet_allowance", "value": 1000, "currency": "PHP", "unit": "Monthly", "payout_frequency": "Monthly" },
    { "key": "target_annual_bonus", "value": 120000, "currency": "PHP", "unit": "Annually", "payout_frequency": "One Time" },
    { "key": "on_target_commission", "value": null, "currency": "PHP", "unit": "Annually", "payout_frequency": "Quarterly" }
  ],

  "isTotalVacationDaysMissing": false,
  "totalVacationDays": 15,
  "defaultVacationDays": 5,
  "statutoryVacationDays": 5,

  "isNoticePeriodMissing": false,
  "noticePeriodType": "STANDARD",
  "noticePeriodInDays": 30,
  "statutoryNoticePeriodInDays": 30,

  "isProbationPeriodMissing": false,
  "probationPeriodQuantity": 6,
  "probationPeriodUnit": "MONTHS",
  "probationPeriodEndDate": "2026-10-17",
  "defaultProbationPeriodQuantity": 6,
  "defaultProbationPeriodUnit": "MONTHS",
  "defaultProbationPeriodEndDate": "2026-10-17",

  "tenureInDays": 365,

  "severanceDays": 30,
  "vacationDaysPayout": 15,

  "mtaDefault": false,
  "mtaDays": null,

  "countryJobFields": null
}
```

**What changed:**

| Field | Before | After |
|---|---|---|
| `compensation` | Split across `yearlySalary`, `targetAnnualBonus`, `onTargetCommission` as separate fields | Single array of all compensation variables with key, value, currency, unit, payout frequency |
| `severanceDays` | Not present — calculated inline by deposit service | Pre-calculated from country config |
| `vacationDaysPayout` | Not present — estimated from `totalVacationDays` | `min(accrued, statutory minimum)` or all accrued |
| `mtaDefault` | Not present | Flag from country config |
| `mtaDays` | Not present | Days to secure MTA (if `mtaDefault = true`) |


