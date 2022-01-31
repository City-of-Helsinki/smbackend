from modeltranslation.translator import TranslationOptions, translator
from bicycle_network.models import BicycleNetwork

class BicycleNetworkTranslationOptions(TranslationOptions):
    fields = ("name",)

translator.register(BicycleNetwork, BicycleNetworkTranslationOptions)