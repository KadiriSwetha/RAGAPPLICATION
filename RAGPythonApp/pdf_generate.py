from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

pdf_path = "Telemetry_Report.pdf"  # Output on your machine

doc = SimpleDocTemplate(pdf_path, pagesize=A4)
styles = getSampleStyleSheet()

content = """
Cummins Engine Telemetry Dashboard
Charts visualizing engine telemetry data within selected timelines such as 24 hours or 48 hours. Metrics
include Engine Temperature, RPM, Oil Pressure, Fuel Consumption Rate, Coolant Temperature, Turbo
Boost Pressure, and recent telemetry entries (last 10 records).- 6 real-time line charts- 5 statistics cards- Recent data table showing last 10 telemetry entries
User Interactions- Hover on charts for detailed values- Auto-scroll for live updates- Zoom using mouse wheel (if enabled)
Upcoming Implementations
1. Quality Monitors
Features:
• Color-coded indicators (Green/Yellow/Red)
• Real-time values
• Mini trend charts
• Threshold information
Use Cases:- Quick health evaluation- Threshold monitoring- Compliance verification
2. Alerts System
Features:
• Severity-based alerts (Critical/Warning/Info)
• Timestamp logging
• Sensor identification
• Actual threshold violation details
Use Cases:- Immediate issue notifications- Threshold violation tracking- Maintenance prioritization
"""

story = [
    Paragraph("Telemetry Dashboard Summary", styles["Title"]),
    Spacer(1, 10),
    Paragraph(content, styles["BodyText"]),
]

doc.build(story)

print("PDF Generated Successfully →", pdf_path)
