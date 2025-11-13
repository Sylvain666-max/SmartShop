from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST 
from .models import Product, Category, ComparisonVote
from django.db.models import Count, Q, F

from products import models

def home(request):
    featured_products = Product.objects.filter(is_featured=True)[:6]
    latest_products = Product.objects.all()[:8]
    categories = Category.objects.all()
    
    # Statistiques globales
    total_products = Product.objects.count()
    amazon_wins = Product.objects.filter(
        amazon_price__lt=F('ebay_price')
    ).count()
    
    context = {
        'featured_products': featured_products,
        'latest_products': latest_products,
        'categories': categories,
        'total_products': total_products,
        'amazon_wins': amazon_wins,
        'page_title': 'SmartShop - Comparateur Amazon vs eBay',
        'meta_description': 'Comparez les prix entre Amazon et eBay. Trouvez les meilleures offres et économisez sur vos achats en ligne.'
    }
    return render(request, 'home.html', context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id)[:4]
    
    # Calculs de comparaison
    best_price = product.get_best_price()
    price_diff = product.get_price_difference()
    
    # Votes pour ce produit
    votes = product.votes.values('platform').annotate(count=Count('platform'))
    vote_stats = {
        'amazon': next((v['count'] for v in votes if v['platform'] == 'amazon'), 0),
        'ebay': next((v['count'] for v in votes if v['platform'] == 'ebay'), 0),
    }
    total_votes = sum(vote_stats.values())
    if total_votes > 0:
        vote_stats['amazon_percent'] = (vote_stats['amazon'] / total_votes) * 100
        vote_stats['ebay_percent'] = (vote_stats['ebay'] / total_votes) * 100
    
    context = {
        'product': product,
        'related_products': related_products,
        'best_price': best_price,
        'price_diff': price_diff,
        'vote_stats': vote_stats,
        'total_votes': total_votes,
        'page_title': product.meta_title,
        'meta_description': product.meta_description,
        'keywords': product.keywords,
    }
    return render(request, 'product_detail.html', context)

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    
    # Filtres
    platform = request.GET.get('platform')
    if platform == 'amazon':
        products = products.filter(amazon_available=True)
    elif platform == 'ebay':
        products = products.filter(ebay_available=True)
    
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        products = products.order_by('base_price')
    elif sort == 'price_high':
        products = products.order_by('-base_price')
    elif sort == 'popular':
        products = products.filter(is_featured=True)
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)
    
    context = {
        'category': category,
        'products': products_page,
        'page_title': f'{category.name} - Comparaison Amazon vs eBay',
        'meta_description': category.meta_description or f'Comparez les prix de {category.name} entre Amazon et eBay'
    }
    return render(request, 'category.html', context)

@require_POST
def vote_platform(request, product_id):
    """Vote pour une plateforme préférée"""
    product = get_object_or_404(Product, id=product_id)
    platform = request.POST.get('platform')
    
    if platform not in ['amazon', 'ebay']:
        return JsonResponse({'error': 'Invalid platform'}, status=400)
    
    ip = request.META.get('REMOTE_ADDR')
    
    try:
        vote, created = ComparisonVote.objects.get_or_create(
            product=product,
            ip_address=ip,
            defaults={'platform': platform}
        )
        
        if not created:
            return JsonResponse({'error': 'Vous avez déjà voté'}, status=400)
        
        # Recalculer les stats
        votes = product.votes.values('platform').annotate(count=Count('platform'))
        vote_stats = {
            'amazon': next((v['count'] for v in votes if v['platform'] == 'amazon'), 0),
            'ebay': next((v['count'] for v in votes if v['platform'] == 'ebay'), 0),
        }
        
        return JsonResponse({
            'success': True,
            'votes': vote_stats
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
