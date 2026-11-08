from django.db import models

# Create your models here.
from django.db import models



class Category(models.Model):
    name = models.CharField(max_length=150, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(max_length=180, unique=True, verbose_name='آدرس دسته‌بندی')
    parent = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='دسته‌بندی والد'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=250, verbose_name='نام محصول')
    slug = models.SlugField(max_length=280, unique=True, verbose_name='آدرس محصول')
    sku = models.CharField(max_length=100, unique=True, verbose_name='کد کالا')

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='دسته‌بندی'
    )

    brand = models.CharField(max_length=150, blank=True, verbose_name='برند')
    short_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='توضیحات کوتاه'
    )
    description = models.TextField(blank=True, verbose_name='توضیحات کامل')

    price = models.PositiveBigIntegerField(
        verbose_name='قیمت (ریال)'
    )

    stock = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    is_active = models.BooleanField(default=True, verbose_name='فعال')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name








class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='محصول'
    )

    image = models.ImageField(
        upload_to='products/%Y/%m/',
        verbose_name='تصویر'
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='توضیح تصویر'
    )

    is_primary = models.BooleanField(
        default=False,
        verbose_name='تصویر اصلی'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'تصویر محصول'
        verbose_name_plural = 'تصاویر محصولات'

    def __str__(self):
        return f'تصویر {self.product.name}'