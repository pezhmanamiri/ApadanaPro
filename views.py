from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product, Category
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST




def home(request):
    return render(request, 'index.html')






def products(request):
    product_list = Product.objects.filter(
        is_active=True
    ).select_related(
        'category'
    ).prefetch_related(
        'images'
    )

    # جست‌وجو بر اساس نام، کد کالا و برند
    search_query = request.GET.get('q', '').strip()

    if search_query:
        product_list = product_list.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(brand__icontains=search_query)
        )

    # فیلتر دسته‌بندی
    selected_category = request.GET.get('category', '')

    if selected_category:
        product_list = product_list.filter(
            category__slug=selected_category
        )

    # فیلتر برند
    selected_brand = request.GET.get('brand', '')

    if selected_brand:
        product_list = product_list.filter(
            brand=selected_brand
        )

    # فقط کالاهای موجود
    in_stock = request.GET.get('in_stock', '')

    if in_stock == '1':
        product_list = product_list.filter(stock__gt=0)

    # حداقل قیمت
    min_price = request.GET.get('min_price', '').strip()

    if min_price.isdigit():
        product_list = product_list.filter(
            price__gte=int(min_price)
        )

    # حداکثر قیمت
    max_price = request.GET.get('max_price', '').strip()

    if max_price.isdigit():
        product_list = product_list.filter(
            price__lte=int(max_price)
        )

    # مرتب‌سازی
    sort = request.GET.get('sort', 'newest')

    if sort == 'cheapest':
        product_list = product_list.order_by('price', '-created_at')
    elif sort == 'expensive':
        product_list = product_list.order_by('-price', '-created_at')
    elif sort == 'name':
        product_list = product_list.order_by('name')
    else:
        sort = 'newest'
        product_list = product_list.order_by('-created_at')

    # صفحه‌بندی
    paginator = Paginator(product_list, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': Category.objects.filter(is_active=True),
        'brands': Product.objects.filter(
            is_active=True
        ).exclude(
            brand=''
        ).values_list(
            'brand', flat=True
        ).distinct().order_by('brand'),

        'search_query': search_query,
        'selected_category': selected_category,
        'selected_brand': selected_brand,
        'in_stock': in_stock,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
    }

    return render(request, 'shop-left-sidebar.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category').prefetch_related('images'),
        slug=slug,
        is_active=True
    )

    return render(request, 'single-product.html', {
        'product': product
    })











def user_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        accepted_terms = request.POST.get('accepted_terms')

        User = get_user_model()

        # بررسی تکمیل فیلدها
        if not all([first_name, last_name, phone, password, confirm_password]):
            messages.error(request, 'لطفاً تمام فیلدها را تکمیل کنید.')

        # بررسی تأیید قوانین
        elif not accepted_terms:
            messages.error(request, 'برای ثبت‌نام باید قوانین سایت را بپذیرید.')

        # بررسی تکراری نبودن شماره موبایل
        elif User.objects.filter(username=phone).exists():
            messages.error(request, 'این شماره موبایل قبلاً ثبت‌نام کرده است.')

        # بررسی یکسان بودن رمزها
        elif password != confirm_password:
            messages.error(request, 'رمز عبور و تکرار آن یکسان نیستند.')

        else:
            try:
                # بررسی قدرت رمز عبور با قوانین Django
                validate_password(password)

                # ساخت حساب کاربری
                user = User.objects.create_user(
                    username=phone,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )

                # ورود خودکار بعد از ثبت‌نام
                authenticated_user = authenticate(
                    request,
                    username=phone,
                    password=password
                )

                if authenticated_user is not None:
                    login(request, authenticated_user)

                messages.success(request, 'ثبت‌نام با موفقیت انجام شد.')
                return redirect('/')

            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)

    return render(request, 'register.html')







def user_login(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=phone,
            password=password
        )

        if user is not None:
            login(request, user)

            if not request.POST.get('remember_me'):
                request.session.set_expiry(0)

            return redirect('/')

        messages.error(request, 'شماره موبایل یا رمز عبور اشتباه است.')

    return render(request, 'login.html')









def user_logout(request):
    if request.method == 'POST':
        logout(request)

    return redirect('/')






@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        quantity = 1

    if quantity > product.stock:
        quantity = product.stock

    cart = request.session.get('cart', {})

    if product.stock > 0:
        current_quantity = cart.get(str(product_id), 0)
        new_quantity = current_quantity + quantity

        cart[str(product_id)] = min(new_quantity, product.stock)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


def cart_detail(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(
        id__in=cart.keys(),
        is_active=True
    )

    cart_items = []
    total_price = 0

    for product in products:
        quantity = cart.get(str(product.id), 0)

        if quantity > product.stock:
            quantity = product.stock

        item_total = product.price * quantity
        total_price += item_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total_price': item_total,
        })

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


@require_POST
def update_cart(request, product_id):
    cart = request.session.get('cart', {})

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = min(quantity, product.stock)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


@require_POST
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    cart.pop(str(product_id), None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')