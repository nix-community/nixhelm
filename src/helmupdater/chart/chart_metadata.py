from pydantic import BaseModel, ConfigDict


class ChartMetadata(BaseModel):
    """Metadata for a Helm chart as stored in Nix files."""

    repo: str
    """URL of the repo"""

    chart: str
    """Name of the chart in the repo"""

    version: str
    chartHash: str

    model_config = ConfigDict(extra="ignore", frozen=True)
