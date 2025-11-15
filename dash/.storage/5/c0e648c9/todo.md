# Automotive Dashboard - Implementation Plan

## Database Structure
- Table: readings
- Key columns: RPM, SPEED, ENGINE_LOAD, timestamp
- Location: /workspace/uploads/auto_data1.db

## Files to Create/Modify

1. **index.html** - Update title to "Automotive Dashboard"

2. **src/pages/Index.tsx** - Main dashboard page
   - Display RPM, Speed, Engine Load in gauge/card format
   - Implement polling mechanism (every 1 second)
   - Fetch latest data from database via API endpoint

3. **src/lib/db.ts** - Database utility functions
   - Function to read latest data from SQLite database
   - Export data fetching functions

4. **api/data.ts** - API endpoint (if needed for backend)
   - Serve latest readings from database
   - Handle CORS and data formatting

5. **src/components/MetricCard.tsx** - Reusable metric display component
   - Display metric name, value, and unit
   - Styled card with automotive theme

6. **src/components/GaugeChart.tsx** - Circular gauge component
   - Visual gauge for RPM and Speed
   - Color-coded based on value ranges

## Implementation Approach
- Use React hooks (useState, useEffect) for state management
- Polling interval: 1000ms (1 second)
- Since this is a frontend app, we'll use a simple approach: copy the database to public folder and read it using sql.js library
- Display metrics in a clean, automotive-themed dashboard layout

## Styling
- Dark theme with blue/green accents (automotive style)
- Large, readable numbers
- Responsive grid layout