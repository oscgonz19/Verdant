# Tutorial 2: Change Detection Analysis

Learn how to detect and quantify vegetation change between time periods.

## Prerequisites

- Completed [Tutorial 1: NDVI Analysis](01-ndvi-analysis.md)
- Understanding of NDVI interpretation

## What You'll Learn

1. Create multi-temporal composites
2. Calculate change (delta) indices
3. Classify change into categories
4. Generate change statistics
5. Interpret and visualize results

---

## Concepts

### What is Change Detection?

Change detection compares satellite imagery from different dates to identify differences:

```
Change = Image(After) - Image(Before)

Negative change → Vegetation decreased (loss)
Zero change     → Vegetation stable
Positive change → Vegetation increased (gain)
```

### Classification Thresholds

Changes are classified into 5 categories:

| Class | dNDVI Range | Interpretation |
|-------|-------------|----------------|
| 1 - Strong Loss | < -0.15 | Major deforestation, fire, development |
| 2 - Moderate Loss | -0.15 to -0.05 | Degradation, partial clearing |
| 3 - Stable | -0.05 to +0.05 | No significant change |
| 4 - Moderate Gain | +0.05 to +0.15 | Regrowth, recovery |
| 5 - Strong Gain | > +0.15 | Afforestation, rapid recovery |

---

## Step 1: Setup

```python
import ee
from engine.composites import create_landsat_composite
from engine.indices import add_ndvi, calculate_delta_indices
from engine.change import classify_change, generate_change_statistics
from engine.config import TEMPORAL_PERIODS

ee.Initialize()

# Define AOI
aoi = ee.Geometry.Rectangle([-62.5, -4.0, -62.0, -3.5])

print("Setup complete!")
```

## Step 2: Create Temporal Composites

```python
def create_period_composite(period_name, aoi):
    """Create a cloud-free composite for a given period."""
    period = TEMPORAL_PERIODS[period_name]

    composite = create_landsat_composite(
        aoi=aoi,
        start_date=period['start'],
        end_date=period['end'],
        sensors=period['sensors'],
        cloud_threshold=20
    )

    # Add NDVI
    composite = add_ndvi(composite)

    return composite

# Create composites for baseline and current
print("Creating 1990s composite...")
composite_1990s = create_period_composite('1990s', aoi)

print("Creating present composite...")
composite_present = create_period_composite('present', aoi)

# Verify image counts
count_1990s = composite_1990s.get('image_count').getInfo()
count_present = composite_present.get('image_count').getInfo()
print(f"1990s: {count_1990s} images, Present: {count_present} images")
```

## Step 3: Calculate Change

```python
# Method 1: Manual calculation
ndvi_before = composite_1990s.select('ndvi')
ndvi_after = composite_present.select('ndvi')
delta_ndvi = ndvi_after.subtract(ndvi_before).rename('dndvi')

# Method 2: Using platform function
delta = calculate_delta_indices(
    before=composite_1990s,
    after=composite_present,
    indices=['ndvi']
)

# Verify delta statistics
delta_stats = delta_ndvi.reduceRegion(
    reducer=ee.Reducer.mean().combine(
        ee.Reducer.stdDev(), sharedInputs=True
    ).combine(
        ee.Reducer.percentile([5, 95]), sharedInputs=True
    ),
    geometry=aoi,
    scale=30,
    maxPixels=1e9
).getInfo()

print("Delta NDVI Statistics:")
print(f"  Mean: {delta_stats['dndvi_mean']:.3f}")
print(f"  Std Dev: {delta_stats['dndvi_stdDev']:.3f}")
print(f"  5th percentile: {delta_stats['dndvi_p5']:.3f}")
print(f"  95th percentile: {delta_stats['dndvi_p95']:.3f}")
```

## Step 4: Classify Changes

```python
from engine.change import classify_change

# Define thresholds
thresholds = {
    'strong_loss': -0.15,
    'moderate_loss': -0.05,
    'moderate_gain': 0.05,
    'strong_gain': 0.15
}

# Classify change
change_map = classify_change(
    delta_image=delta,
    index='ndvi',
    thresholds=thresholds
)

# Class values:
# 1 = Strong Loss
# 2 = Moderate Loss
# 3 = Stable
# 4 = Moderate Gain
# 5 = Strong Gain
```

## Step 5: Generate Statistics

```python
# Calculate area for each class
stats = generate_change_statistics(
    change_map=change_map,
    aoi=aoi,
    scale=30
)

# Display results
print("\nChange Statistics (1990s to Present):")
print("-" * 50)
print(f"{'Class':<20} {'Area (ha)':<15} {'Percent':<10}")
print("-" * 50)

total_area = sum(stats['area_by_class'].values())

for class_name, area in stats['area_by_class'].items():
    percent = (area / total_area) * 100
    print(f"{class_name:<20} {area:>12,.1f}   {percent:>6.1f}%")

print("-" * 50)
print(f"{'Total':<20} {total_area:>12,.1f}")
```

Expected output:

```
Change Statistics (1990s to Present):
--------------------------------------------------
Class                Area (ha)       Percent
--------------------------------------------------
Strong Loss            1,234.5       4.9%
Moderate Loss          2,345.6       9.4%
Stable                15,000.2      60.0%
Moderate Gain          4,567.8      18.3%
Strong Gain            1,852.4       7.4%
--------------------------------------------------
Total                 25,000.5
```

## Step 6: Visualize Results

### Change Map

```python
import geemap

Map = geemap.Map(center=[-3.75, -62.25], zoom=10)

# Color palette for change classes
change_palette = [
    '#d73027',  # 1 - Strong Loss (red)
    '#fc8d59',  # 2 - Moderate Loss (orange)
    '#fee08b',  # 3 - Stable (yellow)
    '#91cf60',  # 4 - Moderate Gain (light green)
    '#1a9850'   # 5 - Strong Gain (dark green)
]

# Add layers
Map.addLayer(
    composite_1990s.select(['red', 'green', 'blue']),
    {'min': 0, 'max': 0.3},
    '1990s True Color',
    shown=False
)

Map.addLayer(
    composite_present.select(['red', 'green', 'blue']),
    {'min': 0, 'max': 0.3},
    'Present True Color',
    shown=False
)

Map.addLayer(
    delta_ndvi,
    {'min': -0.3, 'max': 0.3, 'palette': ['red', 'white', 'green']},
    'Delta NDVI'
)

Map.addLayer(
    change_map,
    {'min': 1, 'max': 5, 'palette': change_palette},
    'Change Classification'
)

# Add legend
Map.add_legend(
    title='Change Class',
    colors=change_palette,
    labels=['Strong Loss', 'Moderate Loss', 'Stable', 'Moderate Gain', 'Strong Gain']
)

Map
```

### Statistics Chart

```python
import matplotlib.pyplot as plt

# Prepare data
classes = list(stats['area_by_class'].keys())
areas = list(stats['area_by_class'].values())
colors = ['#d73027', '#fc8d59', '#fee08b', '#91cf60', '#1a9850']

# Create bar chart
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Bar chart
bars = ax1.bar(classes, areas, color=colors)
ax1.set_ylabel('Area (hectares)')
ax1.set_title('Vegetation Change: 1990s to Present')
ax1.tick_params(axis='x', rotation=45)

# Add value labels
for bar, area in zip(bars, areas):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
             f'{area:,.0f}', ha='center', va='bottom', fontsize=9)

# Pie chart
ax2.pie(areas, labels=classes, colors=colors, autopct='%1.1f%%',
        startangle=90)
ax2.set_title('Change Distribution')

plt.tight_layout()
plt.savefig('change_statistics.png', dpi=300)
plt.show()
```

---

## Full Pipeline Example

Using the high-level orchestrator:

```python
from services.change_orchestrator import ChangeOrchestrator

orchestrator = ChangeOrchestrator()

# Run complete analysis
results = orchestrator.analyze(
    aoi=aoi,
    periods=['1990s', '2000s', '2010s', 'present'],
    indices=['ndvi', 'nbr'],
    reference_period='1990s'
)

# Access results
composites = results['composites']   # Dict of period -> ee.Image
changes = results['changes']         # Dict of comparison -> ee.Image
statistics = results['statistics']   # Dict of comparison -> stats

# Print all statistics
for comparison, stats in statistics.items():
    print(f"\n{comparison}:")
    for class_name, area in stats['area_by_class'].items():
        print(f"  {class_name}: {area:,.1f} ha")
```

---

## Interpreting Results

### What Does Loss Mean?

**Strong Loss (-0.15+ dNDVI):**
- Deforestation / clear-cutting
- Fire damage
- Urban development
- Agricultural conversion
- Mining activity

**Moderate Loss (-0.05 to -0.15 dNDVI):**
- Selective logging
- Forest degradation
- Drought stress
- Disease/pest damage

### What Does Gain Mean?

**Strong Gain (+0.15+ dNDVI):**
- Active reforestation
- Abandoned agriculture recovering
- Post-fire regrowth
- Wetland restoration

**Moderate Gain (+0.05 to +0.15 dNDVI):**
- Natural succession
- Improved land management
- Climate-driven growth

### Validation Tips

1. **Cross-check with high-resolution imagery** (Google Earth, Planet)
2. **Compare multiple indices** (NDVI + NBR for fire detection)
3. **Consider seasonality** (wet vs dry season differences)
4. **Look for spatial patterns** (roads, rivers, boundaries)

---

## Exercises

### Exercise 1: Multi-Period Analysis

Analyze change across all four periods:

```python
periods = ['1990s', '2000s', '2010s', 'present']

all_stats = {}
for i in range(len(periods) - 1):
    before = periods[i]
    after = periods[i + 1]

    results = orchestrator.analyze(
        aoi=aoi,
        periods=[before, after],
        indices=['ndvi'],
        reference_period=before
    )

    key = f"{before}_to_{after}"
    all_stats[key] = results['statistics'][f'{key}_ndvi']

# Compare trends over time
```

### Exercise 2: Compare NDVI vs NBR

```python
results = orchestrator.analyze(
    aoi=aoi,
    periods=['1990s', 'present'],
    indices=['ndvi', 'nbr'],
    reference_period='1990s'
)

# Compare detection capabilities
ndvi_loss = results['statistics']['1990s_to_present_ndvi']['area_by_class']['Strong Loss']
nbr_loss = results['statistics']['1990s_to_present_nbr']['area_by_class']['Strong Loss']

print(f"Strong Loss detected:")
print(f"  NDVI: {ndvi_loss:,.1f} ha")
print(f"  NBR: {nbr_loss:,.1f} ha")
```

### Exercise 3: Custom Thresholds

Test different threshold values:

```python
# More sensitive thresholds (smaller changes detected)
sensitive = {'strong_loss': -0.10, 'moderate_loss': -0.03,
             'moderate_gain': 0.03, 'strong_gain': 0.10}

# Less sensitive (only major changes)
conservative = {'strong_loss': -0.20, 'moderate_loss': -0.08,
                'moderate_gain': 0.08, 'strong_gain': 0.20}

# Compare results...
```

---

## Next Steps

- [Tutorial 3: Custom AOI](03-custom-aoi.md) - Work with complex geometries
- [Tutorial 4: API Integration](04-api-integration.md) - Automate with REST API
