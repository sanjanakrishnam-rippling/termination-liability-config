import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

BLUE = "2563EB"
LIGHT_BLUE = "EFF4FF"
DARK = "1A1A1A"
GRAY = "6B6B6B"
LIGHT_GRAY = "F7F7F5"
GREEN = "16A34A"
GREEN_BG = "F0FDF4"
YELLOW_BG = "FFF9E6"
WHITE = "FFFFFF"
BORDER_COLOR = "E2E2E0"

title_font = Font(name="Calibri", size=14, bold=True, color=DARK)
section_font = Font(name="Calibri", size=12, bold=True, color=BLUE)
header_font = Font(name="Calibri", size=10, bold=True, color=GRAY)
body_font = Font(name="Calibri", size=11, color=DARK)
hint_font = Font(name="Calibri", size=10, italic=True, color=GRAY)
input_font = Font(name="Calibri", size=11, color=BLUE)

fill_header = PatternFill(start_color=LIGHT_BLUE, end_color=LIGHT_BLUE, fill_type="solid")
fill_input = PatternFill(start_color=YELLOW_BG, end_color=YELLOW_BG, fill_type="solid")
fill_white = PatternFill(start_color=WHITE, end_color=WHITE, fill_type="solid")
fill_green = PatternFill(start_color=GREEN_BG, end_color=GREEN_BG, fill_type="solid")
fill_light = PatternFill(start_color=LIGHT_GRAY, end_color=LIGHT_GRAY, fill_type="solid")

thin_border = Border(
    left=Side(style="thin", color=BORDER_COLOR),
    right=Side(style="thin", color=BORDER_COLOR),
    top=Side(style="thin", color=BORDER_COLOR),
    bottom=Side(style="thin", color=BORDER_COLOR),
)

wrap_align = Alignment(wrap_text=True, vertical="top")
center_align = Alignment(horizontal="center", vertical="center")


def style_cell(ws, row, col, value, font=body_font, fill=None, alignment=None, border=None):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = font
    if fill:
        cell.fill = fill
    if alignment:
        cell.alignment = alignment
    if border:
        cell.border = border
    return cell


def add_section_header(ws, row, title):
    style_cell(ws, row, 1, title, font=section_font)
    return row + 1


def add_table_header(ws, row, headers, col_start=1):
    for i, h in enumerate(headers):
        style_cell(ws, row, col_start + i, h, font=header_font, fill=fill_header, border=thin_border,
                   alignment=center_align)
    return row + 1


def add_input_row(ws, row, label, value, hint="", col_start=1, is_input=True):
    style_cell(ws, row, col_start, label, font=body_font, border=thin_border)
    cell = style_cell(ws, row, col_start + 1, value,
                      font=input_font if is_input else body_font,
                      fill=fill_input if is_input else None,
                      border=thin_border)
    if hint:
        style_cell(ws, row, col_start + 2, hint, font=hint_font)
    return row + 1


def add_tier_row(ws, row, from_m, to_m, method, value, col_start=1, is_input=True):
    fill = fill_input if is_input else None
    font = input_font if is_input else body_font
    style_cell(ws, row, col_start, from_m, font=font, fill=fill, border=thin_border, alignment=center_align)
    style_cell(ws, row, col_start + 1, to_m, font=font, fill=fill, border=thin_border, alignment=center_align)
    style_cell(ws, row, col_start + 2, method, font=font, fill=fill, border=thin_border, alignment=center_align)
    style_cell(ws, row, col_start + 3, value, font=font, fill=fill, border=thin_border, alignment=center_align)
    return row + 1


def build_country_sheet(ws, name, data):
    ws.sheet_properties.tabColor = BLUE
    for c in range(1, 10):
        ws.column_dimensions[get_column_letter(c)].width = 22
    ws.column_dimensions["A"].width = 35
    ws.column_dimensions["B"].width = 28

    row = 1
    style_cell(ws, row, 1, f"Termination Liability Configuration — {name}", font=title_font)
    row += 2

    # SECTION 1: General Inputs
    row = add_section_header(ws, row, "1. General Inputs")
    row = add_input_row(ws, row, "Country", data["country"], data.get("country_hint", ""))
    row = add_input_row(ws, row, "Contract Type", data["contract_type"],
                        "Indefinite / Fixed Term")
    if data.get("entity_type"):
        row = add_input_row(ws, row, "Entity Type", data["entity_type"],
                            "Only for countries with multiple employment models")
    else:
        row = add_input_row(ws, row, "Entity Type", "N/A",
                            "Only for DE, FR, BE — leave N/A otherwise", is_input=False)
    row = add_input_row(ws, row, "Is MTA the default practice?", data["mta_default"],
                        "Yes / No")
    row += 1

    # SECTION 2: MTA Configuration (if applicable)
    row = add_section_header(ws, row, "2. MTA Configuration (if MTA = Yes)")
    if data["mta_default"] == "Yes":
        row = add_input_row(ws, row, "Days to secure MTA (average)", data["mta_days"],
                            "Fixed number of days")
        row += 1
        style_cell(ws, row, 1, "MTA Severance Tiers", font=Font(name="Calibri", size=11, bold=True, color=DARK))
        row += 1
        tier_headers = ["From (tenure months)", "To (tenure months)", "Method", "Value"]
        row = add_table_header(ws, row, tier_headers)
        for t in data["mta_tiers"]:
            row = add_tier_row(ws, row, t[0], t[1], t[2], t[3])
        style_cell(ws, row, 1, "Max cap (days)", font=body_font, border=thin_border)
        style_cell(ws, row, 2, data.get("mta_max_cap", "None"), font=input_font, fill=fill_input, border=thin_border)
        row += 1
        style_cell(ws, row, 1, "↳ Add more tiers as needed by inserting rows above", font=hint_font)
    else:
        style_cell(ws, row, 1, "N/A — MTA is not the default for this country", font=hint_font)
    row += 2

    # SECTION 3: Severance Cost Components
    row = add_section_header(ws, row, "3. Severance Cost Components")

    if data["contract_type"] == "Fixed Term":
        row = add_input_row(ws, row, "Use remaining days on contract as severance?",
                            data.get("use_remaining_contract_days", "No"), "Yes / No — if Yes, skip tier table below")
        row += 1

    for ci, comp in enumerate(data["components"]):
        style_cell(ws, row, 1,
                   f"Component {ci + 1}: {comp['label']}" + (" (default)" if comp.get("is_default") else ""),
                   font=Font(name="Calibri", size=11, bold=True, color=DARK))
        row += 1
        row = add_table_header(ws, row, ["From (tenure months)", "To (tenure months)", "Method", "Value"])
        for t in comp["tiers"]:
            row = add_tier_row(ws, row, t[0], t[1], t[2], t[3])
        style_cell(ws, row, 1, "Max cap (days)", font=body_font, border=thin_border)
        style_cell(ws, row, 2, comp.get("max_cap", "None"), font=input_font, fill=fill_input, border=thin_border)
        row += 1
        style_cell(ws, row, 1, "↳ Add more tiers by inserting rows above this line", font=hint_font)
        row += 2

    style_cell(ws, row, 1, "↳ To add another component, copy a component block above and change the label",
               font=hint_font)
    row += 2

    # SECTION 4: Vacation Payout
    row = add_section_header(ws, row, "4. Vacation Payout")
    row = add_input_row(ws, row, "Pay out accrued vacation during termination?",
                        data["vacation"]["enabled"], "Yes / No")
    if data["vacation"]["enabled"] == "Yes":
        row = add_input_row(ws, row, "What is the minimum that needs to be paid out?",
                            data["vacation"]["minimum"], "All Accrued / Fixed number of days")
        if data["vacation"]["minimum"] == "Fixed number of days":
            row += 1
            style_cell(ws, row, 1, "Vacation Payout Tiers",
                       font=Font(name="Calibri", size=11, bold=True, color=DARK))
            row += 1
            row = add_table_header(ws, row, ["From (tenure months)", "To (tenure months)", "Method", "Value"])
            for t in data["vacation"]["tiers"]:
                row = add_tier_row(ws, row, t[0], t[1], t[2], t[3])
            style_cell(ws, row, 1, "Max cap (days)", font=body_font, border=thin_border)
            style_cell(ws, row, 2, data["vacation"].get("max_cap", "None"),
                       font=input_font, fill=fill_input, border=thin_border)
            row += 1
            style_cell(ws, row, 1, "↳ Add more tiers by inserting rows above this line", font=hint_font)
    row += 2

    # SECTION 5: Compensation Variable Metadata
    row = add_section_header(ws, row, "5. Compensation Variable Metadata")
    style_cell(ws, row, 1,
               "For each compensation variable, indicate Yes/No for each column. New variables default to No.",
               font=hint_font)
    row += 1
    cv_headers = ["Compensation Variable", "Included in Working Notice?", "Included in Severance?",
                  "Included in Vacation Pay?"]
    row = add_table_header(ws, row, cv_headers)
    for cv in data["comp_vars"]:
        style_cell(ws, row, 1, cv[0], font=body_font, border=thin_border)
        for j in range(1, 4):
            style_cell(ws, row, j + 1, cv[j], font=input_font, fill=fill_input, border=thin_border,
                       alignment=center_align)
        row += 1
    style_cell(ws, row, 1, "↳ Add more variables by inserting rows above", font=hint_font)
    row += 2

    # SECTION 6: Worked Examples
    examples = data.get("examples", [])
    if examples:
        row = add_section_header(ws, row, "6. Worked Examples — How Severance & Vacation Pay Are Calculated")
        style_cell(ws, row, 1,
                   "These examples show how the config above translates into actual severance days and dollar amounts.",
                   font=hint_font)
        row += 2

        example_label_font = Font(name="Calibri", size=11, bold=True, color=DARK)
        step_font = Font(name="Calibri", size=11, color=DARK)
        result_font = Font(name="Calibri", size=11, bold=True, color=GREEN)
        calc_font = Font(name="Calibri", size=11, color=BLUE)

        for ex_idx, ex in enumerate(examples):
            style_cell(ws, row, 1, f"Example {ex_idx + 1}: {ex['title']}", font=section_font)
            row += 1

            # Employee profile
            style_cell(ws, row, 1, "Employee Profile", font=example_label_font)
            row += 1
            for label, val in ex["profile"]:
                style_cell(ws, row, 1, f"  {label}", font=step_font, border=thin_border)
                style_cell(ws, row, 2, val, font=calc_font, border=thin_border)
                row += 1
            row += 1

            # Severance calculation
            style_cell(ws, row, 1, "Severance Calculation", font=example_label_font)
            row += 1
            for step in ex["severance_steps"]:
                if step.startswith("→"):
                    style_cell(ws, row, 1, step, font=result_font)
                elif step.startswith("="):
                    style_cell(ws, row, 1, f"  {step}", font=calc_font)
                else:
                    style_cell(ws, row, 1, f"  {step}", font=step_font)
                row += 1
            row += 1

            # Vacation calculation
            if ex.get("vacation_steps"):
                style_cell(ws, row, 1, "Vacation Payout Calculation", font=example_label_font)
                row += 1
                for step in ex["vacation_steps"]:
                    if step.startswith("→"):
                        style_cell(ws, row, 1, step, font=result_font)
                    elif step.startswith("="):
                        style_cell(ws, row, 1, f"  {step}", font=calc_font)
                    else:
                        style_cell(ws, row, 1, f"  {step}", font=step_font)
                    row += 1
                row += 1

            # Total
            if ex.get("total_steps"):
                style_cell(ws, row, 1, "What Gets Passed to Risk", font=example_label_font)
                row += 1
                for step in ex["total_steps"]:
                    if step.startswith("→"):
                        style_cell(ws, row, 1, step, font=result_font)
                    else:
                        style_cell(ws, row, 1, f"  {step}", font=step_font)
                    row += 1
            row += 2

        style_cell(ws, row, 1,
                   "Note: Risk converts severance_days into a dollar amount using the severance salary basis (comp variables marked 'Included in Severance = Yes').",
                   font=hint_font)
        row += 1
        style_cell(ws, row, 1,
                   "Note: Risk converts vacation_days_payout into a dollar amount using the vacation pay salary basis (comp variables marked 'Included in Vacation Pay = Yes').",
                   font=hint_font)
        row += 2

    # SECTION 7: Notes / Items Not Captured
    section_num = 7 if examples else 6
    row = add_section_header(ws, row, f"{section_num}. Notes / Items Not Captured")
    style_cell(ws, row, 1, "Use this section to flag anything the config above cannot express:", font=hint_font)
    row += 1
    for note in data.get("notes", []):
        style_cell(ws, row, 1, f"• {note}", font=body_font)
        row += 1

    return ws


# ========== INSTRUCTIONS TAB ==========
ws_instr = wb.active
ws_instr.title = "Instructions"
ws_instr.sheet_properties.tabColor = "16A34A"
ws_instr.column_dimensions["A"].width = 80

instructions = [
    ("Termination Liability Configuration — Instructions", title_font),
    ("", body_font),
    ("Purpose", section_font),
    ("This spreadsheet captures termination cost rules per country for EOR deposit estimation.", body_font),
    ("It mirrors the Termination Liability Config UI and is used to pressure-test whether we can", body_font),
    ("configure rules for different countries using the proposed model.", body_font),
    ("", body_font),
    ("How to Use", section_font),
    ("1. Go to the 'Template' tab → right-click → 'Duplicate' → rename to your country (e.g., 'Germany')", body_font),
    ("2. Fill in all yellow-highlighted cells with the correct values for that country", body_font),
    ("3. Add or remove tier rows as needed (insert rows within the tier tables)", body_font),
    ("4. If a section doesn't apply, leave it as-is or write 'N/A'", body_font),
    ("5. Use the 'Notes' section at the bottom to flag anything the template can't express", body_font),
    ("", body_font),
    ("Reference Tabs", section_font),
    ("• Philippines — completed example (simple: no MTA, per-year severance, all accrued vacation)", body_font),
    ("• Spain — completed example (two dismissal types with different rates and max caps, pagas extra)", body_font),
    ("• Template — blank template to duplicate for new countries", body_font),
    ("", body_font),
    ("Field Definitions", section_font),
    ("", body_font),
    ("General Inputs:", Font(name="Calibri", size=11, bold=True, color=DARK)),
    ("• Country — country code and name", body_font),
    ("• Contract Type — 'Indefinite' or 'Fixed Term'", body_font),
    ("• Entity Type — only for countries with multiple employment models (e.g., Germany: AUG / Consultant)", body_font),
    ("• Is MTA the default? — whether Rippling typically negotiates a mutual termination agreement", body_font),
    ("", body_font),
    ("Tier Model:", Font(name="Calibri", size=11, bold=True, color=DARK)),
    ("• From / To (tenure months) — the tenure bracket this rule applies to (use 'No limit' for open-ended)", body_font),
    ("• Method — 'Fixed' (flat number of days) or 'Per year of service' (days × years of tenure)", body_font),
    ("• Value — the number of days (e.g., '30 days' or '15 days per year of service')", body_font),
    ("• Max cap (days) — optional ceiling on total days for this component (write 'None' if no cap)", body_font),
    ("", body_font),
    ("Compensation Variable Metadata:", Font(name="Calibri", size=11, bold=True, color=DARK)),
    ("• Included in Working Notice? — is this comp variable paid during the working notice period?", body_font),
    ("• Included in Severance? — is this comp variable included in the severance salary basis?", body_font),
    ("• Included in Vacation Pay? — is this comp variable included in the vacation pay salary basis?", body_font),
    ("", body_font),
    ("Validation Rules:", Font(name="Calibri", size=11, bold=True, color=DARK)),
    ("• No negative values — all numeric fields must be zero or positive", body_font),
    ("• Fractional days allowed (e.g., 1.5 days per year of service)", body_font),
    ("• Tenure months must be whole numbers", body_font),
    ("• Tiers must be contiguous — no gaps (e.g., 0–12 then 24–60 is invalid; 12–24 must exist)", body_font),
    ("", body_font),
    ("Out of Scope (v1):", Font(name="Calibri", size=11, bold=True, color=DARK)),
    ("• Historical salary lookbacks / trailing averages — we use current compensation only", body_font),
    ("• Pre-probation vs post-probation rules — captured implicitly via tenure tiers", body_font),
    ("• Financial reserve payments (e.g., 10% of salary)", body_font),
    ("• Special pay types specific to one country (e.g., Colombia integral salary)", body_font),
    ("", body_font),
    ("Questions?", section_font),
    ("Slack Sanjana Krishnam or comment in the Notes section of each country tab.", body_font),
]

for i, (text, font) in enumerate(instructions):
    cell = ws_instr.cell(row=i + 1, column=1, value=text)
    cell.font = font


# ========== PHILIPPINES TAB ==========
ph_data = {
    "country": "Philippines (PH)",
    "contract_type": "Indefinite",
    "entity_type": None,
    "mta_default": "No",
    "mta_days": None,
    "mta_tiers": [],
    "components": [
        {
            "label": "Redundancy Pay",
            "is_default": True,
            "tiers": [
                (0, "No limit", "Per year of service", "30 days per year of service"),
            ],
            "max_cap": "None",
        }
    ],
    "vacation": {
        "enabled": "Yes",
        "minimum": "All Accrued",
        "tiers": [],
    },
    "comp_vars": [
        ("Gross Base Salary", "Yes", "Yes", "Yes"),
        ("Target Bonus", "Yes", "No", "No"),
        ("Signing Bonus", "Yes", "No", "No"),
        ("On-Target Commission", "Yes", "No", "No"),
        ("Rice Allowance", "Yes", "No", "No"),
        ("Uniform & Clothing Allowance", "Yes", "No", "No"),
        ("Laundry Allowance", "Yes", "No", "No"),
        ("Medical Cash Allowance", "Yes", "No", "No"),
        ("Internet Allowance", "Yes", "No", "No"),
        ("Productivity Incentive Allowance", "Yes", "No", "No"),
        ("Christmas / Anniversary Gift", "Yes", "No", "No"),
        ("13th Month Salary", "Yes", "No", "No"),
    ],
    "examples": [
        {
            "title": "Employee with 2.5 years tenure",
            "profile": [
                ("Tenure", "2 years, 6 months (2.5 years)"),
                ("Gross Base Salary", "₱100,000 / month"),
                ("Rice Allowance", "₱2,000 / month"),
                ("Internet Allowance", "₱1,000 / month"),
                ("Accrued Vacation Balance", "18 days"),
            ],
            "severance_steps": [
                "Step 1: Identify the matching tier for tenure = 30 months",
                "  Tier: 0 → No limit months, Method: Per year of service, Value: 30 days/yr",
                "Step 2: Calculate severance days",
                "  Tenure = 2.5 years × 30 days/yr = 75 days",
                "Step 3: Check max cap",
                "  Max cap = None → no cap applies",
                "→ severance_days = 75",
                "",
                "Step 4: Determine severance salary basis (comp vars where Severance = Yes)",
                "  Only 'Gross Base Salary' is included in severance",
                "  Severance daily rate = ₱100,000 / 30 = ₱3,333.33",
                "Step 5: Calculate severance pay",
                "= 75 days × ₱3,333.33 = ₱250,000",
                "→ Severance pay = ₱250,000",
            ],
            "vacation_steps": [
                "Config says: All Accrued",
                "Employee has 18 days accrued",
                "→ vacation_days_payout = 18",
                "",
                "Vacation pay salary basis (comp vars where Vacation Pay = Yes):",
                "  Only 'Gross Base Salary' is included",
                "  Vacation daily rate = ₱100,000 / 30 = ₱3,333.33",
                "= 18 days × ₱3,333.33 = ₱60,000",
                "→ Vacation payout = ₱60,000",
            ],
            "total_steps": [
                "severance_days = 75 (passed to Risk role bean)",
                "vacation_days_payout = 18 (passed to Risk role bean)",
                "→ Risk uses the salary bases above to convert days → dollar amounts for deposit sizing",
            ],
        },
        {
            "title": "Employee with 8 months tenure (< 1 year)",
            "profile": [
                ("Tenure", "8 months (0.67 years)"),
                ("Gross Base Salary", "₱80,000 / month"),
                ("Accrued Vacation Balance", "5 days"),
            ],
            "severance_steps": [
                "Step 1: Identify the matching tier for tenure = 8 months",
                "  Tier: 0 → No limit months, Method: Per year of service, Value: 30 days/yr",
                "Step 2: Calculate severance days",
                "  Tenure = 0.67 years × 30 days/yr = 20 days",
                "Step 3: Check max cap → None",
                "→ severance_days = 20",
            ],
            "vacation_steps": [
                "Config says: All Accrued",
                "Employee has 5 days accrued",
                "→ vacation_days_payout = 5",
            ],
            "total_steps": [
                "severance_days = 20",
                "vacation_days_payout = 5",
                "→ Passed to Risk role bean for deposit calculation",
            ],
        },
    ],
    "notes": [
        "In PH, full compensation is paid during notice period, but severance uses base salary only.",
        "13th Month Salary is mandatory and always included in working notice.",
    ],
}

ws_ph = wb.create_sheet("Philippines")
build_country_sheet(ws_ph, "Philippines", ph_data)


# ========== SPAIN TAB ==========
es_data = {
    "country": "Spain (ES)",
    "contract_type": "Indefinite",
    "entity_type": None,
    "mta_default": "No",
    "mta_days": None,
    "mta_tiers": [],
    "components": [
        {
            "label": "Severance — Unfair Dismissal (Improcedente)",
            "is_default": True,
            "tiers": [
                (0, "No limit", "Per year of service", "33 days per year of service"),
            ],
            "max_cap": "720",
        },
        {
            "label": "Severance — Objective Dismissal (Procedente)",
            "is_default": False,
            "tiers": [
                (0, "No limit", "Per year of service", "20 days per year of service"),
            ],
            "max_cap": "360",
        },
    ],
    "vacation": {
        "enabled": "Yes",
        "minimum": "All Accrued",
        "tiers": [],
    },
    "comp_vars": [
        ("Gross Base Salary", "Yes", "Yes", "Yes"),
        ("Pagas Extra (13th/14th Month)", "Yes", "Yes", "Yes"),
        ("Target Bonus", "Yes", "No", "No"),
        ("On-Target Commission", "Yes", "No", "No"),
        ("Meal Allowance", "Yes", "No", "No"),
        ("Transport Allowance", "Yes", "No", "No"),
    ],
    "examples": [
        {
            "title": "Employee with 5 years tenure — Unfair Dismissal",
            "profile": [
                ("Tenure", "5 years (60 months)"),
                ("Gross Base Salary", "€4,000 / month"),
                ("Pagas Extra (13th/14th)", "€8,000 / year (= €666.67 / month equivalent)"),
                ("Target Bonus", "€6,000 / year"),
                ("Accrued Vacation Balance", "12 days"),
            ],
            "severance_steps": [
                "Step 1: We use the WORST CASE component for deposit sizing → Unfair Dismissal",
                "  Tier: 0 → No limit months, Method: Per year of service, Value: 33 days/yr",
                "",
                "Step 2: Calculate severance days",
                "  Tenure = 5 years × 33 days/yr = 165 days",
                "",
                "Step 3: Check max cap",
                "  Max cap = 720 days (24 months' salary) → 165 < 720, no cap applies",
                "→ severance_days = 165",
                "",
                "Step 4: Determine severance salary basis (comp vars where Severance = Yes)",
                "  Gross Base Salary: €4,000/month ✓",
                "  Pagas Extra: €666.67/month ✓",
                "  Target Bonus: ✗ (not in severance basis)",
                "  Total monthly severance basis = €4,666.67",
                "  Daily rate = €4,666.67 / 30 = €155.56",
                "",
                "Step 5: Calculate severance pay",
                "= 165 days × €155.56 = €25,667",
                "→ Severance pay = €25,667",
            ],
            "vacation_steps": [
                "Config says: All Accrued",
                "Employee has 12 days accrued",
                "→ vacation_days_payout = 12",
                "",
                "Vacation pay salary basis (comp vars where Vacation Pay = Yes):",
                "  Gross Base Salary: €4,000/month ✓",
                "  Pagas Extra: €666.67/month ✓",
                "  Daily rate = €4,666.67 / 30 = €155.56",
                "= 12 days × €155.56 = €1,866.67",
                "→ Vacation payout = €1,866.67",
            ],
            "total_steps": [
                "severance_days = 165 (passed to Risk role bean)",
                "vacation_days_payout = 12 (passed to Risk role bean)",
                "→ Risk uses the salary bases to convert → total deposit exposure = €25,667 + €1,866.67 = €27,534",
            ],
        },
        {
            "title": "Employee with 30 years tenure — Cap applies",
            "profile": [
                ("Tenure", "30 years (360 months)"),
                ("Gross Base Salary", "€5,000 / month"),
                ("Pagas Extra (13th/14th)", "€10,000 / year (= €833.33 / month equivalent)"),
                ("Accrued Vacation Balance", "22 days"),
            ],
            "severance_steps": [
                "Step 1: Use Unfair Dismissal component (worst case)",
                "  Tier: 0 → No limit months, Method: Per year of service, Value: 33 days/yr",
                "",
                "Step 2: Calculate severance days (before cap)",
                "  Tenure = 30 years × 33 days/yr = 990 days",
                "",
                "Step 3: Check max cap",
                "  Max cap = 720 days → 990 > 720, CAP APPLIES",
                "→ severance_days = 720 (capped)",
                "",
                "Step 4: Severance salary basis",
                "  Base + Pagas Extra = €5,000 + €833.33 = €5,833.33/month",
                "  Daily rate = €5,833.33 / 30 = €194.44",
                "",
                "Step 5: Calculate severance pay",
                "= 720 days × €194.44 = €140,000",
                "→ Severance pay = €140,000",
                "",
                "Without the cap it would have been 990 × €194.44 = €192,500 — the cap saves €52,500",
            ],
            "vacation_steps": [
                "Config says: All Accrued",
                "Employee has 22 days accrued",
                "→ vacation_days_payout = 22",
                "= 22 × €194.44 = €4,278",
                "→ Vacation payout = €4,278",
            ],
            "total_steps": [
                "severance_days = 720 (capped from 990)",
                "vacation_days_payout = 22",
                "→ Total deposit exposure = €140,000 + €4,278 = €144,278",
                "→ This demonstrates why the max cap matters — it prevents runaway liability for long-tenured employees",
            ],
        },
    ],
    "notes": [
        "Spain has two severance rates depending on dismissal classification. For deposit sizing, we should model the worst case (unfair dismissal = 33 days/yr, 24 month cap) since most challenged dismissals are reclassified as unfair.",
        "The config captures both objective (20 days/yr) and unfair (33 days/yr) as separate components. In practice, only one applies per termination — Risk should use the higher one for deposit estimation.",
        "Pre-Feb 2012 hires have a transitional rule: 45 days/yr (capped at 42 months) for pre-reform service. This cannot be expressed in the current tier model — flag for custom logic if material.",
        "Pagas extra (extraordinary payments) are 2 extra monthly payments per year, typically paid in June and December. They are included in the severance salary basis.",
        "Prorated pagas extra must also be paid out at termination (final settlement / finiquito).",
        "15-day notice period required for objective dismissals. No notice required for disciplinary dismissals.",
    ],
}

ws_es = wb.create_sheet("Spain")
build_country_sheet(ws_es, "Spain", es_data)


# ========== TEMPLATE TAB ==========
template_data = {
    "country": "",
    "country_hint": "Enter country name and code, e.g., 'Germany (DE)'",
    "contract_type": "",
    "entity_type": None,
    "mta_default": "",
    "mta_days": "",
    "mta_tiers": [
        ("", "", "", ""),
    ],
    "mta_max_cap": "",
    "components": [
        {
            "label": "Redundancy Pay",
            "is_default": True,
            "tiers": [
                ("", "", "", ""),
                ("", "", "", ""),
            ],
            "max_cap": "",
        }
    ],
    "vacation": {
        "enabled": "",
        "minimum": "",
        "tiers": [
            ("", "", "", ""),
        ],
        "max_cap": "",
    },
    "comp_vars": [
        ("Gross Base Salary", "", "", ""),
        ("", "", "", ""),
        ("", "", "", ""),
        ("", "", "", ""),
        ("", "", "", ""),
    ],
    "notes": [
        "",
        "",
        "",
    ],
}

ws_tmpl = wb.create_sheet("Template")
ws_tmpl.sheet_properties.tabColor = "D97706"
build_country_sheet(ws_tmpl, "[Country Name]", template_data)

output_path = "/Users/sanjana/Desktop/termination-liability-config/Termination_Liability_Config.xlsx"
wb.save(output_path)
print(f"Saved to {output_path}")
