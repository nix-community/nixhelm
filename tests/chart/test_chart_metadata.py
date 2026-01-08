import pytest
from pydantic import ValidationError

from helmupdater.chart import ChartMetadata


class TestChartMetadata:
    """Test ChartMetadata Pydantic model."""

    def test_valid_init(self, chart_metadata_dict):
        chart = ChartMetadata(**chart_metadata_dict)

        assert chart.repo == chart_metadata_dict["repo"]
        assert chart.chart == chart_metadata_dict["chart"]
        assert chart.version == chart_metadata_dict["version"]
        assert chart.chartHash == chart_metadata_dict["chartHash"]

    def test_missing_data(self):
        with pytest.raises(ValidationError):
            ChartMetadata()  # type: ignore

    def test_extra_fields_ignored(self, chart_metadata_dict):
        chart = ChartMetadata(**chart_metadata_dict, extra_field="ignore me")  # type: ignore

        assert chart.repo == chart_metadata_dict["repo"]
        assert chart.chart == chart_metadata_dict["chart"]
        assert not hasattr(chart, "extra_field")
