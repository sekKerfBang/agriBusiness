import re
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from functools import partial

# Validateur SIRET
@deconstructible
class SIRETValidator:
    message = "Le SIRET doit contenir exactement 14 chiffres"
    code = 'invalid_siret'
    
    def __init__(self, message=None):
        if message:
            self.message = message
    
    def __call__(self, value):
        if not re.match(r'^\d{14}$', value):
            raise ValidationError(self.message, code=self.code)
    
    def __eq__(self, other):
        return isinstance(other, SIRETValidator) and self.message == other.message

# Validateur téléphone français
@deconstructible
class FrenchPhoneValidator:
    message = "Numéro de téléphone français invalide"
    code = 'invalid_phone'
    
    def __call__(self, value):
        pattern = r'^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$'
        if not re.match(pattern, value):
            raise ValidationError(self.message, code=self.code)

# Validateur taille image
@deconstructible
class ImageSizeValidator:
    def __init__(self, max_size_mb=5):
        self.max_size = max_size_mb * 1024 * 1024
    
    def __call__(self, value):
        if value.size > self.max_size:
            raise ValidationError(f"Image trop volumineuse (max {self.max_size / 1024 / 1024}MB)")
    
    def __eq__(self, other):
        return isinstance(other, ImageSizeValidator) and self.max_size == other.max_size

# Partial pour créer des validateurs rapides
validate_siret = partial(SIRETValidator)
validate_phone = partial(FrenchPhoneValidator)
validate_image_5mb = partial(ImageSizeValidator, 5)


# import re
# from django.core.exceptions import ValidationError
# from functools import partial

# # Partial pour validation SIRET
# validate_siret = partial(
#     lambda value: re.match(r'^\d{14}$', value) is not None,
#     message="Le SIRET doit contenir 14 chiffres"
# )

# def validate_phone_french(value):
#     """Validateur pour numéro français"""
#     pattern = r'^(0|\+33)[1-9](\d{2}){4}$'
#     if not re.match(pattern, value):
#         raise ValidationError("Numéro de téléphone invalide")

# # Partial pour validation d'image
# validate_image_size = partial(
#     lambda img: img.size <= 5 * 1024 * 1024,  # 5MB
#     message="L'image ne doit pas dépasser 5MB"
# )