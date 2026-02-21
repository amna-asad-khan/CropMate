from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class CropRecommendation(models.Model):
    """
    Model to store crop recommendation predictions
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    
    # Input parameters
    nitrogen = models.FloatField(help_text="Nitrogen content in soil (kg/ha)")
    phosphorus = models.FloatField(help_text="Phosphorus content in soil (kg/ha)")
    potassium = models.FloatField(help_text="Potassium content in soil (kg/ha)")
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Relative humidity in %")
    ph = models.FloatField(help_text="pH value of the soil")
    rainfall = models.FloatField(help_text="Rainfall in mm")
    
    # Output
    recommended_crop = models.CharField(max_length=100, help_text="Recommended crop")
    confidence = models.FloatField(null=True, blank=True, help_text="Prediction confidence")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Crop Recommendation'
        verbose_name_plural = 'Crop Recommendations'
    
    def __str__(self):
        return f"{self.user.username} - {self.recommended_crop} ({self.created_at.strftime('%Y-%m-%d')})"
