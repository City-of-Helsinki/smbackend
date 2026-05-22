from unittest.mock import MagicMock, patch

from django.test import TestCase

from services.api import KmlRenderer

ERROR_KML = "<?xml version='1.0' encoding='UTF-8'?>\n<kml>\n  <Document>\n    <Placemark>\n      <name>Error: No data found or invalid request.</name>\n    </Placemark>\n  </Document>\n</kml>"


class KmlRendererTest(TestCase):
    def _make_renderer_context(self, status_code):
        response = MagicMock()
        response.status_code = status_code
        return {"response": response}

    def test_400_status_code_returns_error_kml(self):
        renderer = KmlRenderer()
        renderer_context = self._make_renderer_context(400)

        with patch("services.api.render_to_string", return_value=ERROR_KML) as mock_rts:
            result = renderer.render(
                {}, "application/vnd.google-earth.kml+xml", renderer_context
            )
            mock_rts.assert_called_once_with("kml.xml", {"places": [], "lang_code": ""})

        self.assertEqual(result, ERROR_KML)

    def test_404_status_code_returns_error_kml(self):
        renderer = KmlRenderer()
        renderer_context = self._make_renderer_context(404)

        with patch("services.api.render_to_string", return_value=ERROR_KML) as mock_rts:
            result = renderer.render(
                {}, "application/vnd.google-earth.kml+xml", renderer_context
            )
            mock_rts.assert_called_once_with("kml.xml", {"places": [], "lang_code": ""})

        self.assertEqual(result, ERROR_KML)
