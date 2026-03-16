"""
Example usage of the FactorCalculator package.

This file demonstrates various ways to use the factor_calculator package
for calculating trading factors using DMU and PEU units.
"""

import datetime
import pandas as pd

# Import the package
from factor_calculator import (
    FactorCalculator,
    SimpleFactorCalculator,
    create_unit,
    create_units,
    get_available_classes,
    parse_unit_spec,
)


# Example 1: Parse unit specifications
def example_parse_specs():
    """Demonstrate parsing unit specifications."""
    print("=" * 60)
    print("Example 1: Parsing Unit Specifications")
    print("=" * 60)
    
    specs = [
        "KlineDMU(45)",
        "KlineDMU(interval=5)",
        "BiquotePEU(watching_time=60)",
        "PositionPnlDMU",
    ]
    
    for spec in specs:
        class_name, params = parse_unit_spec(spec)
        print(f"  {spec!r}")
        print(f"    -> class: {class_name}, params: {params!r}")
    print()


# Example 2: List available units
def example_list_units():
    """Demonstrate listing available units."""
    print("=" * 60)
    print("Example 2: Listing Available Units")
    print("=" * 60)
    
    print("All available units:")
    for cls in get_available_classes():
        print(f"  - {cls}")
    
    print("\nDMU classes only:")
    for cls in get_available_classes("DMU"):
        print(f"  - {cls}")
    
    print("\nPEU classes only:")
    for cls in get_available_classes("PEU"):
        print(f"  - {cls}")
    print()


# Example 3: Create unit instances
def example_create_units():
    """Demonstrate creating unit instances."""
    print("=" * 60)
    print("Example 3: Creating Unit Instances")
    print("=" * 60)
    
    # Create a single unit
    unit = create_unit("KlineDMU(interval=5)")
    print(f"Created: {unit}")
    print(f"  Name: {unit.name}")
    print(f"  Interval: {unit.interval}")
    print()
    
    # Create multiple units
    units = create_units([
        "PositionPnlDMU",
        "TrendDMU",
    ])
    print(f"Created {len(units)} units:")
    for u in units:
        print(f"  - {u.name}")
    print()


# Example 4: Using SimpleFactorCalculator
def example_simple_calculator():
    """Demonstrate SimpleFactorCalculator usage."""
    print("=" * 60)
    print("Example 4: SimpleFactorCalculator")
    print("=" * 60)
    
    # Create sample market data
    md_data = pd.DataFrame({
        "name": pd.date_range("2024-03-15 09:30", periods=10, freq="1min"),
        "last_px": [100.0 + i * 0.1 for i in range(10)],
        "tot_sz": [100 * (i + 1) for i in range(10)],
        "oi": [1000 + i * 10 for i in range(10)],
    })
    md_data.set_index("name", inplace=True)
    
    # Initialize calculator (requires a valid db directory)
    # calc = SimpleFactorCalculator(db_directory="/path/to/db")
    
    # Calculate DMU (requires RBT to be installed and configured)
    # result = calc.calculate_dmu(
    #     dmu_spec="PassThroughDMU",
    #     contract="IF2403",
    #     trade_date="2024-03-15",
    #     md_data=md_data,
    # )
    # print(result)
    
    print("Note: SimpleFactorCalculator requires:")
    print("  - RBT package installed")
    print("  - Valid database directory")
    print("  - Market data in proper format")
    print()


# Example 5: Using FactorCalculator with full RBT integration
def example_full_calculator():
    """Demonstrate FactorCalculator with full RBT integration."""
    print("=" * 60)
    print("Example 5: FactorCalculator (Full Integration)")
    print("=" * 60)
    
    # This requires:
    # - A result database directory with stored factors
    # - Market data directory with tick data
    # - RBT package properly configured
    
    # Example initialization:
    # calc = FactorCalculator(
    #     db_directory="/path/to/results",
    #     md_directory="/path/to/market/data",
    # )
    
    # Example calculation:
    # result = calc.calculate(
    #     units=[
    #         "KlineDMU(interval=5)",
    #         "BiquotePEU(watching_time=60)",
    #     ],
    #     load_factors=["KlineDMU__open", "KlineDMU__close"],
    #     contract="IF2403",
    #     trade_date="2024-03-15",
    #     frequency="tick",
    # )
    
    print("Note: FactorCalculator requires:")
    print("  - RBT package installed and configured")
    print("  - Valid result database directory")
    print("  - Market data files in RBT format")
    print()
    print("Example usage:")
    print("""
    from factor_calculator import FactorCalculator
    
    calc = FactorCalculator(
        db_directory="/path/to/results",
        md_directory="/path/to/market/data",
    )
    
    result = calc.calculate(
        units=[
            "KlineDMU(interval=5)",
            "BiquotePEU(watching_time=60)",
        ],
        load_factors=["KlineDMU__open"],
        contract="IF2403",
        trade_date="2024-03-15",
    )
    
    print(result)
    """)


# Example 6: CLI usage
def example_cli():
    """Demonstrate CLI usage."""
    print("=" * 60)
    print("Example 6: CLI Usage")
    print("=" * 60)
    
    print("""
# List available units
factor-calculator list
factor-calculator list --dmu
factor-calculator list --peu

# Calculate factors
factor-calculator calculate \\
    --db /path/to/results \\
    --md /path/to/market/data \\
    --units "KlineDMU(5),BiquotePEU(60)" \\
    --contract IF2403 \\
    --date 2024-03-15

# Show existing factors
factor-calculator factors \\
    --db /path/to/results \\
    --contract IF2403 \\
    --date 2024-03-15
    """)


# Run all examples
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("FactorCalculator Package Examples")
    print("=" * 60 + "\n")
    
    example_parse_specs()
    example_list_units()
    example_create_units()
    example_simple_calculator()
    example_full_calculator()
    example_cli()
