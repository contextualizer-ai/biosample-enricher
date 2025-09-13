"""Pydantic models for soil enrichment data."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SoilObservation(BaseModel):
    """Individual soil measurement or prediction at a location."""

    # Soil Classification
    classification_usda: str | None = Field(
        None,
        description="USDA Soil Taxonomy classification (e.g., 'Typic Haplocryepts')",
    )
    classification_wrb: str | None = Field(
        None, description="WRB soil classification (e.g., 'Cambisols')"
    )
    confidence_usda: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in USDA classification (0-1)"
    )
    confidence_wrb: float | None = Field(
        None, ge=0.0, le=1.0, description="Confidence in WRB classification (0-1)"
    )

    # Physical Properties
    ph_h2o: float | None = Field(
        None, ge=0.0, le=14.0, description="Soil pH in water (0-14 scale)"
    )
    organic_carbon: float | None = Field(
        None, ge=0.0, description="Soil organic carbon content (g/kg)"
    )
    bulk_density: float | None = Field(
        None, ge=0.0, description="Soil bulk density (g/cm³)"
    )

    # Texture Properties
    sand_percent: float | None = Field(
        None, ge=0.0, le=100.0, description="Sand content percentage"
    )
    silt_percent: float | None = Field(
        None, ge=0.0, le=100.0, description="Silt content percentage"
    )
    clay_percent: float | None = Field(
        None, ge=0.0, le=100.0, description="Clay content percentage"
    )
    texture_class: str | None = Field(
        None, description="USDA texture class (e.g., 'Loam', 'Sandy clay loam')"
    )

    # Chemical Properties
    total_nitrogen: float | None = Field(
        None, ge=0.0, description="Total nitrogen content (g/kg)"
    )
    available_phosphorus: float | None = Field(
        None, ge=0.0, description="Available phosphorus content (mg/kg)"
    )
    cation_exchange_capacity: float | None = Field(
        None, ge=0.0, description="Cation exchange capacity (cmol(c)/kg)"
    )

    # Measurement Context
    depth_cm: str | None = Field(
        None, description="Depth interval (e.g., '0-5cm', '5-15cm')"
    )
    measurement_method: str | None = Field(
        None, description="Measurement or prediction method"
    )

    @field_validator("texture_class")
    @classmethod
    def validate_texture_class(cls, v: str | None) -> str | None:
        """Validate USDA texture class names."""
        if v is None:
            return None

        valid_classes = {
            "Sand",
            "Loamy sand",
            "Sandy loam",
            "Loam",
            "Silt loam",
            "Silt",
            "Sandy clay loam",
            "Clay loam",
            "Silty clay loam",
            "Sandy clay",
            "Silty clay",
            "Clay",
        }

        if v not in valid_classes:
            # Allow for variations in casing/formatting
            normalized = v.title()
            if normalized not in valid_classes:
                raise ValueError(
                    f"Invalid texture class: {v}. Must be one of {valid_classes}"
                )
            return normalized

        return v


class SoilResult(BaseModel):
    """Results from soil enrichment for a specific location."""

    # Location Context
    latitude: float = Field(description="Latitude of measurement location")
    longitude: float = Field(description="Longitude of measurement location")
    distance_m: float | None = Field(
        None,
        ge=0.0,
        description="Distance from requested location to measurement (meters)",
    )

    # Soil Data
    observations: list[SoilObservation] = Field(
        default_factory=list, description="Soil observations at different depths"
    )

    # Data Quality
    quality_score: float = Field(
        ge=0.0, le=1.0, description="Overall data quality score (0-1)"
    )
    provider: str = Field(description="Data source provider")
    retrieved_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the data was retrieved"
    )

    # Error Information
    errors: list[str] = Field(
        default_factory=list, description="Any errors encountered during retrieval"
    )
    warnings: list[str] = Field(
        default_factory=list, description="Any warnings about data quality"
    )

    def to_nmdc_schema(self) -> dict[str, Any]:
        """Convert to NMDC biosample schema format."""
        result: dict[str, Any] = {}

        # Get surface soil observation (0-5cm or first available)
        surface_obs = self._get_surface_observation()
        if not surface_obs:
            return result

        # Soil type mapping
        if surface_obs.classification_usda or surface_obs.classification_wrb:
            classifications = []
            if surface_obs.classification_usda:
                classifications.append(f"{surface_obs.classification_usda} [USDA]")
            if surface_obs.classification_wrb:
                classifications.append(f"{surface_obs.classification_wrb} [WRB]")

            result["soil_type"] = {
                "has_raw_value": " / ".join(classifications),
                "type": "nmdc:TextValue",
            }

        # pH mapping
        if surface_obs.ph_h2o is not None:
            result["ph"] = {
                "has_numeric_value": surface_obs.ph_h2o,
                "has_unit": "pH",
                "type": "nmdc:QuantityValue",
            }

        # Texture method mapping
        if surface_obs.texture_class:
            result["soil_texture_meth"] = (
                f"USDA texture classification: {surface_obs.texture_class}"
            )

        # Add source information
        result["_soil_enrichment_source"] = self.provider
        result["_soil_enrichment_quality"] = float(self.quality_score)

        return result

    def to_gold_schema(self) -> dict[str, Any]:
        """Convert to GOLD biosample schema format."""
        result: dict[str, Any] = {}

        surface_obs = self._get_surface_observation()
        if not surface_obs:
            return result

        # Add to habitat description
        habitat_details = []
        if surface_obs.classification_usda:
            habitat_details.append(f"Soil: {surface_obs.classification_usda}")
        if surface_obs.texture_class:
            habitat_details.append(f"Texture: {surface_obs.texture_class}")
        if surface_obs.ph_h2o is not None:
            habitat_details.append(f"pH: {surface_obs.ph_h2o}")

        if habitat_details:
            result["habitatDetails"] = "; ".join(habitat_details)

        # Environmental parameters
        env_params: dict[str, float] = {}
        if surface_obs.ph_h2o is not None:
            env_params["soil_ph"] = surface_obs.ph_h2o
        if surface_obs.organic_carbon is not None:
            env_params["soil_organic_carbon_g_kg"] = surface_obs.organic_carbon
        if surface_obs.total_nitrogen is not None:
            env_params["soil_total_nitrogen_g_kg"] = surface_obs.total_nitrogen

        if env_params:
            result["environmentalParameters"] = env_params

        return result

    def _get_surface_observation(self) -> SoilObservation | None:
        """Get the surface soil observation (0-5cm preferred)."""
        if not self.observations:
            return None

        # Prefer 0-5cm depth if available
        for obs in self.observations:
            if obs.depth_cm and "0-5" in obs.depth_cm:
                return obs

        # Return first observation as fallback
        return self.observations[0]


# USDA Texture Classification Constants
USDA_TEXTURE_CLASSES = {
    "Sand": {"sand": (85, 100), "clay": (0, 10)},
    "Loamy sand": {"sand": (70, 85), "clay": (0, 15)},
    "Sandy loam": {"sand": (50, 70), "clay": (0, 20)},
    "Loam": {"sand": (23, 52), "clay": (7, 27), "silt": (28, 50)},
    "Silt loam": {"sand": (0, 50), "clay": (0, 27), "silt": (50, 88)},
    "Silt": {"sand": (0, 20), "clay": (0, 12), "silt": (80, 100)},
    "Sandy clay loam": {"sand": (45, 80), "clay": (20, 35)},
    "Clay loam": {"sand": (20, 45), "clay": (27, 40)},
    "Silty clay loam": {"sand": (0, 20), "clay": (27, 40)},
    "Sandy clay": {"sand": (45, 65), "clay": (35, 55)},
    "Silty clay": {"sand": (0, 20), "clay": (40, 60)},
    "Clay": {"sand": (0, 45), "clay": (40, 100)},
}


def classify_texture(sand_pct: float, silt_pct: float, clay_pct: float) -> str:
    """Classify soil texture using USDA texture triangle.

    Args:
        sand_pct: Sand percentage (0-100)
        silt_pct: Silt percentage (0-100)
        clay_pct: Clay percentage (0-100)

    Returns:
        USDA texture class name

    Raises:
        ValueError: If percentages don't sum to ~100% or are invalid
    """
    # Validate inputs
    total = sand_pct + silt_pct + clay_pct
    if not (95 <= total <= 105):  # Allow for small rounding errors
        raise ValueError(f"Sand + silt + clay must sum to ~100%, got {total}%")

    if any(pct < 0 or pct > 100 for pct in [sand_pct, silt_pct, clay_pct]):
        raise ValueError("All percentages must be between 0 and 100")

    # Normalize to exactly 100%
    factor = 100.0 / total
    sand = sand_pct * factor
    silt = silt_pct * factor
    clay = clay_pct * factor

    # Apply USDA texture triangle rules
    # Rules are applied in order of specificity

    if clay >= 40:
        if sand >= 45:
            return "Sandy clay"
        elif silt >= 40:
            return "Silty clay"
        else:
            return "Clay"

    elif clay >= 27:
        if sand >= 45:
            return "Sandy clay loam"
        elif silt >= 28 and silt < 50:
            return "Clay loam"
        else:  # silt >= 50
            return "Silty clay loam"

    elif clay >= 20:
        if sand >= 45:
            return "Sandy clay loam"
        else:
            return "Clay loam"

    elif silt >= 80:
        return "Silt"

    elif silt >= 50:
        return "Silt loam"

    elif sand >= 85:
        return "Sand"

    elif sand >= 70:
        return "Loamy sand"

    elif sand >= 50:
        return "Sandy loam"

    else:
        return "Loam"
