from django.db import models
from django.contrib.auth.models import User

class Taxe(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=100)

    def __str__(self):
        return self.nom

class Paiement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    taxes = models.ManyToManyField(Taxe)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    stripe_checkout_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.montant_total}€"
