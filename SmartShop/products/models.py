from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Classe Bootstrap Icon")
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=200)
    image = models.ImageField(upload_to='products/')
    
    # Prix et disponibilité
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Prix de référence")
    
    # Amazon
    amazon_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amazon_link = models.URLField(blank=True)
    amazon_available = models.BooleanField(default=True)
    amazon_rating = models.DecimalField(max_digits=2, decimal_places=1, 
                                        validators=[MinValueValidator(0), MaxValueValidator(5)],
                                        null=True, blank=True)
    amazon_reviews = models.IntegerField(default=0)
    amazon_shipping = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    amazon_delivery_days = models.IntegerField(default=2, help_text="Jours de livraison")
    
    # eBay
    ebay_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ebay_link = models.URLField(blank=True)
    ebay_available = models.BooleanField(default=True)
    ebay_rating = models.DecimalField(max_digits=2, decimal_places=1,
                                      validators=[MinValueValidator(0), MaxValueValidator(5)],
                                      null=True, blank=True)
    ebay_reviews = models.IntegerField(default=0)
    ebay_shipping = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    ebay_delivery_days = models.IntegerField(default=5, help_text="Jours de livraison")
    
    # SEO et métadonnées
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    keywords = models.CharField(max_length=200, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_best_price(self):
        """Retourne le meilleur prix disponible"""
        prices = []
        if self.amazon_available and self.amazon_price:
            prices.append({
                'platform': 'Amazon',
                'total': float(self.amazon_price + self.amazon_shipping),
                'price': float(self.amazon_price),
                'shipping': float(self.amazon_shipping)
            })
        if self.ebay_available and self.ebay_price:
            prices.append({
                'platform': 'eBay',
                'total': float(self.ebay_price + self.ebay_shipping),
                'price': float(self.ebay_price),
                'shipping': float(self.ebay_shipping)
            })
        
        return min(prices, key=lambda x: x['total']) if prices else None
    
    def get_price_difference(self):
        """Calcule la différence de prix entre Amazon et eBay"""
        if self.amazon_price and self.ebay_price:
            amazon_total = float(self.amazon_price + self.amazon_shipping)
            ebay_total = float(self.ebay_price + self.ebay_shipping)
            diff = abs(amazon_total - ebay_total)
            percentage = (diff / min(amazon_total, ebay_total)) * 100
            return {
                'difference': diff,
                'percentage': round(percentage, 1),
                'cheaper': 'Amazon' if amazon_total < ebay_total else 'eBay'
            }
        return None
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = f"{self.title} - Comparaison Amazon vs eBay"
        if not self.meta_description:
            self.meta_description = f"Comparez les prix de {self.title} sur Amazon et eBay. Trouvez la meilleure offre !"
        super().save(*args, **kwargs)

class ComparisonVote(models.Model):
    """Votes des utilisateurs pour leur plateforme préférée"""
    PLATFORM_CHOICES = [
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='votes')
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['product', 'ip_address']
