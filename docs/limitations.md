# Real-World Limitations & Academic Prototype Notice

## 1. Academic Disclaimer
> **"The system is intended as an academic AI-based traffic safety decision-support prototype. Real-world deployment would require validated sensors/data sources, extensive field testing, safety certification, regulatory compliance, redundancy, and professional traffic-engineering validation."**

---

## 2. Specific Scope & Constraints

1. **Non-Autonomous Decision Support**:
   - This application is an advisory, decision-support prototype.
   - It does not directly actuate vehicle brakes, throttles, or certified municipal traffic signals.

2. **Kinematic vs Real-World Pavement Variations**:
   - The physics model assumes nominal dry asphalt friction ($\mu = 0.70$).
   - Environmental variations (standing water, ice, gravel, oil slicks, tyre wear, slope) are not modeled in this prototype.

3. **Human Reaction Time & Driver Perception**:
   - In real-world intersections, Perception-Reaction Time (PRT) typically introduces an additional $1.0\text{s}$ to $1.5\text{s}$ latency before braking initiation occurs.
   - The decision directives here reflect instantaneous kinematic state evaluation.

4. **Data Provenance Transparency**:
   - In accordance with academic honesty requirements, user inputs are strictly labeled as **"User Provided Traffic Data"**.
   - No manual data entry is ever mislabeled as "Live IoT Hardware Sensor Data".
