# Dataset Documentation: Physics-Based Blind-Corner Collision Development Dataset

**Dataset Name**: `blind_corner_traffic_dataset.csv`  
**Version**: 1.0.0  
**Type**: Synthetic Kinematic Development Dataset (Explicitly labeled — NOT real-world sensor telemetry)  
**Academic Role**: Decision-Support ML Training & Evaluation Prototype

---

## 1. Provenance & Academic Transparency Notice
This dataset was synthetically synthesized using classical Newtonian kinematics, stopping-distance physics, and intersection conflict-zone geometry. **It is NOT collected from physical road telemetry or real-world crash records.**

Public vehicular trajectory datasets (e.g., NGSIM, HighD, CitySim) focus on highway car-following or multi-lane roundabouts, which do not align with our specific paired dual-approach blind-corner problem formulation. Hence, a physics-grounded development dataset was generated under rigorous physical parameters.

---

## 2. Mathematical & Physical Principles Used

### 2.1 Velocity & Kinematics
- Approach speed conversion:
  $$v_{\text{cm/s}} = v_{\text{km/h}} \times \frac{250}{9} \approx 27.778 \times v_{\text{km/h}}$$
- Time-to-Collision (conflict entry time):
  $$\text{TTC} = \begin{cases} \frac{d}{v_{\text{cm/s}}}, & \text{if } v > 0 \\ \infty \text{ (imputed to 99.0s)}, & \text{if } v = 0 \end{cases}$$

### 2.2 Braking & Stopping Distance
Using standard dry asphalt friction coefficient $\mu = 0.70$ and gravitational acceleration $g = 980 \text{ cm/s}^2$:
$$d_{\text{stop}} = \frac{v_{\text{cm/s}}^2}{2 \mu g} = \frac{v_{\text{cm/s}}^2}{1372}$$

If the current distance to the corner $d < d_{\text{stop}}$, the vehicle cannot stop before entering the blind conflict point.

### 2.3 Conflict Zone Intersection & Labeling
- **COLLISION_RISK**: Both vehicles are simultaneously approaching, their arrival time difference $|TTC_A - TTC_B| \le 0.40\text{s}$, combined stopping distances exceed corner proximity, and estimated TTC is critical ($\le 1.0\text{s}$).
- **HIGH_RISK**: Either simultaneous approach with arrival difference $\le 1.2\text{s}$ and TTC $\le 2.0\text{s}$, or one approach has critical stopping distance deficit with blind queue presence.
- **CAUTION**: One vehicle approaching moderately (TTC between $2.0\text{s}$ and $4.5\text{s}$), or elevated traffic density (queue $\ge 2$) with moderate speeds.
- **SAFE**: Distances are large, speeds are near zero, vehicle counts are zero, or vehicles are stationary.

---

## 3. Class Distribution & Imbalance
The generator employs stratified physical parameter sampling to ensure all four classes (`SAFE`, `CAUTION`, `HIGH_RISK`, `COLLISION_RISK`) are represented with realistic variance and boundary overlap, preventing trivial separability.

---

## 4. Limitations
1. **Academic Prototype Only**: Does not account for variable pavement friction (rain, ice), tire condition, driver perception-reaction delay, or vehicle geometry.
2. **Deterministic Geometry**: Assumes perpendicular 90-degree blind corner without intermediate visual line-of-sight.
3. **No Safety Certification**: This dataset and the resulting models must NOT be used for autonomous vehicle safety or uncertified real-world traffic control.
