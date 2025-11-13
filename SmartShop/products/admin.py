from django.contrib import admin
from .models import Product, Category, ComparisonVote

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'amazon_price', 'ebay_price', 
                    'get_winner', 'is_featured', 'created_at']
    list_filter = ['category', 'is_featured', 'amazon_available', 'ebay_available']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'description']
    list_editable = ['is_featured']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('title', 'slug', 'category', 'short_description', 
                      'description', 'image', 'base_price', 'is_featured')
        }),
        ('Amazon', {
            'fields': ('amazon_price', 'amazon_link', 'amazon_available',
                      'amazon_rating', 'amazon_reviews', 'amazon_shipping', 
                      'amazon_delivery_days'),
            'classes': ('collapse',)
        }),
        ('eBay', {
            'fields': ('ebay_price', 'ebay_link', 'ebay_available',
                      'ebay_rating', 'ebay_reviews', 'ebay_shipping',
                      'ebay_delivery_days'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'keywords'),
            'classes': ('collapse',)
        }),
    )
    
    def get_winner(self, obj):
        best = obj.get_best_price()
        if best:
            return f"🏆 {best['platform']}"
        return "N/A"
    get_winner.short_description = 'Gagnant'

@admin.register(ComparisonVote)
class ComparisonVoteAdmin(admin.ModelAdmin):
    list_display = ['product', 'platform', 'ip_address', 'created_at']
    list_filter = ['platform', 'created_at']
    search_fields = ['product__title']
