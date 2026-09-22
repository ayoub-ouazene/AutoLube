from pydantic import BaseModel, Field




class SearchInput(BaseModel):
    brand: str = Field(description="Car brand, e.g., Renault, Dacia, Volkswagen")
    model: str = Field(description="Car model, e.g., Duster, Golf, Symbol")
    year: int = Field(description="Production year as integer, e.g., 2018")

    engine: str = Field(
        default="",
        description=(
            "Engine code or displacement. "
            "REQUIRED for Engine Oil and Oil Filter (e.g., '1.5 dCi 90', 'EP6FDT 156 THP'). "
            "OPTIONAL for Gearbox Oil — provide only if the user mentioned it, as extra context "
            "that helps disambiguate variants. Never put the gearbox code in this field."
        )
    )

    gearbox_ref: str = Field(
        default="",
        description=(
            "Gearbox reference / ccode ONLY — REQUIRED for Gearbox Oil. "
            "Examples: 'MQ250', 'TL4', 'MA5', 'DQ250', '02Q'. "
            "Do NOT include the transmission type here — that goes in transmission_type."
            "Leave empty otherwise."
        )
    )

    transmission_type: str = Field(
        default="",
        description=(
            "Transmission type — REQUIRED for Gearbox Oil. "
            "One of: 'Manual', 'Automatic', 'DSG/DCT', 'CVT'. "
            "Leave empty otherwise."
        )
    )

    mileage: int = Field(description="Current vehicle mileage in km, e.g., 180000")
    fluid_type: str = Field(description="Fluid type: Engine Oil, Gearbox Oil, or Oil Filter")


class StockLookupInput(BaseModel):
    fluid_type: str = Field(
        description="One of: 'Engine Oil', 'Gearbox Oil', 'Oil Filter'."
    )
    oem_specification: str = Field(
        default="",
        description=(
            "Engine Oil: OEM spec, e.g. 'VW 507.00' or 'RN0720'. "
            "Gearbox Oil: OEM fluid reference, e.g. 'VW G 052 171 A2' or 'Renault NFJ'. "
            "Oil Filter: part reference, e.g. 'Purflux LS946' or '03N115562B'."
        ),
    )
    viscosity: str = Field(
        default="",
        description="Viscosity grade, e.g. '5W-30', '75W-80'. Not applicable to filters.",
    )


class SpecsLookupInput(BaseModel):
    fluid_type: str = Field(description="One of: 'Engine Oil', 'Gearbox Oil'.")
    brand: str = Field(description="Car brand, e.g. 'Renault', 'Volkswagen'.")
    model: str = Field(description="Car model, e.g. 'Clio IV', 'Golf VII'.")
    year: int = Field(description="Production year, e.g. 2018.")
    engine: str = Field(
        default="",
        description="Engine code/displacement. Required for Engine Oil. e.g. 'K9K 646', '1.5 dCi 110'.",
    )
    gearbox_ref: str = Field(
        default="",
        description="Gearbox reference. Required for Gearbox Oil. e.g. 'MQ250', 'TL4'.",
    )
    transmission_type: str = Field(
        default="",
        description="One of: 'Manual', 'Automatic', 'DSG/DCT', 'CVT'. Required for Gearbox Oil.",
    )

