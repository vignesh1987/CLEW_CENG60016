import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="CLEW Nexus: What Breaks First?",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("# CLEW Nexus: What Breaks First?")

col_sliders, col_results = st.columns([1.2, 1.8])

with col_sliders:
    st.subheader("System Parameters")
    
    # Add reset button at top
    if st.button("🔄 Reset", use_container_width=False):
        st.session_state.clear()
        st.rerun()
    
    st.write("**Population & Demand**")
    population = st.slider(
        "Population (Millions)",
        min_value=5, max_value=15, value=5, step=1
    )
    
    diet_intensity = st.slider(
        "Diet Intensity (kg food/person/year)",
        min_value=200, max_value=600, value=200, step=25,
        help="Higher = more meat, more water/land needed"
    )
    
    energy_per_capita = st.slider(
        "Energy Use per Capita (kWh/year)",
        min_value=100, max_value=500, value=100, step=50
    )
    
    st.write("**Agriculture**")
    irrigation_share = st.slider(
        "Irrigated Land Share (%)",
        min_value=0, max_value=100, value=0, step=10,
        help="% of food production using irrigation"
    )
    
    st.write("**Energy Mix**")
    renewable_share = st.slider(
        "Renewable Share (%)",
        min_value=0, max_value=100, value=0, step=10,
        help="Solar/wind (land intensive)"
    )
    
    st.write("**Transport**")
    biofuel_share = st.slider(
        "Biofuel for Transport (%)",
        min_value=0, max_value=30, value=0, step=5,
        help="% of transport energy from biofuels"
    )
    
    st.markdown("---")
    st.subheader("Resource Constraints")
    
    col_land, col_water = st.columns(2)
    with col_land:
        arable_land = st.number_input(
            "Arable Land (M hectares)",
            min_value=5, max_value=200, value=5, step=5
        )
    with col_water:
        water_availability = st.number_input(
            "Water Availability (B m³/year)",
            min_value=5, max_value=50, value=5, step=5
        )

with col_results:
    st.subheader("Constraints & Outputs")
    
    # Define baseline diet intensity for proportional scaling
    baseline_diet_intensity = 200  # kg/person/year
    diet_proportionality_factor = diet_intensity / baseline_diet_intensity
    
    # Calculate food demand
    food_demand = population * diet_intensity / 1000
    
    # Land for food - irrigation increases productivity
    # Rainfed: 2 tons/hectare, Irrigated: 5 tons/hectare
    rainfed_share = (100 - irrigation_share) / 100
    irrigated_share = irrigation_share / 100
    rainfed_productivity = 2.0  # tons/ha
    irrigated_productivity = 5.0  # tons/ha
    avg_productivity = (rainfed_share * rainfed_productivity) + (irrigated_share * irrigated_productivity)
    land_for_food = food_demand / avg_productivity
    
    # Calculate total energy
    total_energy = population * energy_per_capita / 1000  # GWh
    
    # Add energy for irrigation (pumping water)
    # Irrigated agriculture: ~0.5 GWh per million tons of food
    irrigation_energy = (food_demand * (irrigation_share / 100)) * 0.5
    total_energy += irrigation_energy
    
    renewable_energy = total_energy * renewable_share / 100
    fossil_energy = total_energy * (100 - renewable_share) / 100
    
    # Land constraint (renewables are land-intensive)
    # Solar/wind: ~5-10 hectares per GWh (average)
    land_for_renewables = renewable_energy * 8  # hectares
    
    # Biofuel for transport
    transport_energy = population * 0.15  # Assume transport is 15% of total energy demand
    biofuel_energy = transport_energy * biofuel_share / 100
    land_for_biofuel = biofuel_energy * 10  # Biofuel: ~10 hectares per GWh (crop intensive)
    
    # Water constraint (fossil fuels need cooling water)
    # Coal/gas plants: ~2-5 m³ per MWh
    water_for_fossil = fossil_energy * 3  # m³ (in billion equivalent)
    # Irrigated water scales proportionally with diet intensity
    water_for_food = (food_demand * (irrigation_share / 100)) * 2.0 * diet_proportionality_factor  # Irrigated: 2.0 B m³/M tons
    water_for_food += (food_demand * ((100 - irrigation_share) / 100)) * 0.3 * diet_proportionality_factor  # Rainfed: 0.3 B m³/M tons
    water_for_biofuel = biofuel_energy * 1.5  # Biofuel crops need irrigation
    
    # Emissions - absolute emissions (total, not per capita)
    # Factor to achieve ~10 Mt CO2/year at baseline (population=10M, energy=100 kWh/cap, 0% renewable)
    fossil_emissions = (fossil_energy * 10000) / 1000  # Million tons CO2/year
    biofuel_emissions = (biofuel_energy * 1000) / 1000  # Million tons CO2/year
    total_emissions = fossil_emissions + biofuel_emissions
    
    # Check constraints
    total_land_needed = land_for_food + land_for_renewables + land_for_biofuel
    land_violation = total_land_needed > arable_land
    land_surplus_deficit = total_land_needed - arable_land
    
    total_water_needed = water_for_food + water_for_fossil + water_for_biofuel
    water_violation = total_water_needed > water_availability
    water_surplus_deficit = total_water_needed - water_availability
    
    # Display constraint status
    st.write("**🚨 CONSTRAINT STATUS**")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if land_violation:
            overshoot = land_surplus_deficit
            st.error(f"⚠️ LAND EXCEEDED\n\n**Need:** {total_land_needed:.1f}M ha\n\n**Available:** {arable_land}M ha\n\n**Overshoot:** +{overshoot:.1f}M ha ({(overshoot/arable_land)*100:.0f}%)")
        else:
            st.success(f"💚 LAND OK\n\n{arable_land - total_land_needed:.1f}M ha remaining\n\nUsage: {(total_land_needed/arable_land)*100:.0f}%")
    
    with c2:
        if water_violation:
            overshoot_w = water_surplus_deficit
            st.error(f"⚠️ WATER EXCEEDED\n\n**Need:** {total_water_needed:.1f}B m³\n\n**Available:** {water_availability}B m³\n\n**Overshoot:** +{overshoot_w:.1f}B m³ ({(overshoot_w/water_availability)*100:.0f}%)")
        else:
            st.success(f"💚 WATER OK\n\n{water_availability - total_water_needed:.1f}B m³ remaining\n\nUsage: {(total_water_needed/water_availability)*100:.0f}%")
    
    with c3:
        st.metric("Total Emissions", f"{total_emissions:.1f} Mt CO2/year")
    
    st.markdown("---")
    
    # Key outputs
    st.write("**Key Metrics**")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Food Demand", f"{food_demand:.1f}M tons", f"{population}M people")
    m2.metric("Total Energy", f"{total_energy:.1f} GWh", f"{energy_per_capita} kWh/cap")
    m3.metric("Renewable Energy", f"{renewable_energy:.1f} GWh", f"{renewable_share}%")
    m4.metric("Land Needed", f"{total_land_needed:.1f}M ha", f"of {arable_land}M available")
    
    st.markdown("---")
    
    # Constraint visualization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Constraint usage
        land_pct = (total_land_needed/arable_land)*100
        water_pct = (total_water_needed/water_availability)*100
        
        fig = go.Figure(data=[go.Bar(
            x=['Land', 'Water'],
            y=[land_pct, water_pct],
            marker=dict(color=['#d62728' if land_violation else '#2ca02c',
                               '#d62728' if water_violation else '#1f77b4']),
            text=[f"{land_pct:.0f}%", f"{water_pct:.0f}%"],
            textposition='auto'
        )])
        fig.update_layout(
            title="Constraint Usage (100% = limit)",
            yaxis_range=[0, 150],
            yaxis_title="% of Limit",
            height=350,
            showlegend=False,
            shapes=[dict(type="line", x0=-0.5, x1=1.5, y0=100, y1=100, 
                        line=dict(color="red", width=2, dash="dash"))]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Land competition
        fig = go.Figure(data=[
            go.Bar(name='Food', x=['Land'], y=[land_for_food], marker_color='#ff7f0e'),
            go.Bar(name='Renewables', x=['Land'], y=[land_for_renewables], marker_color='#2ca02c'),
            go.Bar(name='Biofuel', x=['Land'], y=[land_for_biofuel], marker_color='#d62728')
        ])
        fig.update_layout(
            title="Land Competition",
            yaxis_title="M hectares",
            height=350,
            shapes=[dict(type="line", x0=-0.5, x1=0.5, y0=arable_land, y1=arable_land,
                        line=dict(color="red", width=2, dash="dash"))]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Water competition
        fig = go.Figure(data=[
            go.Bar(name='Food', x=['Water'], y=[water_for_food], marker_color='#ff7f0e'),
            go.Bar(name='Fossil Fuels', x=['Water'], y=[water_for_fossil], marker_color='#d62728'),
            go.Bar(name='Biofuel', x=['Water'], y=[water_for_biofuel], marker_color='#ff6b6b')
        ])
        fig.update_layout(
            title="Water Competition",
            yaxis_title="B m³/year",
            height=350,
            shapes=[dict(type="line", x0=-0.5, x1=0.5, y0=water_availability, y1=water_availability,
                        line=dict(color="red", width=2, dash="dash"))]
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.subheader("💡 What Breaks First?")

if land_violation and not water_violation:
    st.error(f"🔴 **LAND breaks first** - Overshooting by {land_surplus_deficit:.1f}M ha ({(land_surplus_deficit/arable_land)*100:.0f}%)")
elif water_violation and not land_violation:
    st.error(f"🔴 **WATER breaks first** - Overshooting by {water_surplus_deficit:.1f}B m³ ({(water_surplus_deficit/water_availability)*100:.0f}%)")
elif land_violation and water_violation:
    st.error(f"🔴 **BOTH break** - Land +{land_surplus_deficit:.1f}M ha, Water +{water_surplus_deficit:.1f}B m³")
else:
    st.success("🟢 **System balanced** - But emissions still rising with fossil fuels")

st.write(f"""
**Emissions Breakdown:**
- **Fossil Fuels**: {fossil_emissions:.3f} Mt CO2/year
- **Biofuels**: {biofuel_emissions:.3f} Mt CO2/year  
- **Total**: {total_emissions:.3f} Mt CO2/year
""")
