from custom_components.orvibo_remote.const import MODEL_ALLONE, MODEL_ALLONE_PRO
from custom_components.orvibo_remote.orvibo_client import OrviboClient


def test_detect_capabilities_allone() -> None:
    capabilities = OrviboClient.detect_capabilities(
        hardware_type="irda",
        model_hint=MODEL_ALLONE,
        enable_rf=False,
    )
    assert capabilities.model == MODEL_ALLONE
    assert capabilities.ir_supported is True
    assert capabilities.rf_supported is False


def test_detect_capabilities_allone_pro() -> None:
    capabilities = OrviboClient.detect_capabilities(
        hardware_type="irda",
        model_hint=MODEL_ALLONE_PRO,
        enable_rf=True,
    )
    assert capabilities.model == MODEL_ALLONE_PRO
    assert capabilities.ir_supported is True
    assert capabilities.rf_supported is True
