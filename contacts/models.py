from django.db import models
from django.utils import timezone
import stripe
import logging

logger = logging.getLogger(__name__)

class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.email}"

class ProjectInquiry(models.Model):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='inquiry')
    package = models.ForeignKey('projects.ProjectPackage', on_delete=models.SET_NULL, null=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    timeline = models.JSONField(default=dict)
    converted_to_order = models.BooleanField(default=False)
    converted_at = models.DateTimeField(null=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-contact__created_at"]
        verbose_name = "Project Inquiry"
        verbose_name_plural = "Project Inquiries"

    def __str__(self):
        return f"Inquiry from {self.contact.name} - {self.package.get_name_display() if self.package else 'No package'}"

    # Your existing methods are correct
    def create_stripe_customer(self):
        if not self.stripe_customer_id and self.contact.email:
            try:
                customer = stripe.Customer.create(
                    email=self.contact.email,
                    metadata={
                        'inquiry_id': self.id,
                        'package': self.package.name
                    }
                )
                self.stripe_customer_id = customer.id
                self.save()
                return customer
            except stripe.error.StripeError as e:
                logger.error(f"Stripe customer creation failed: {e}")
                return None

    def convert_to_order(self, user):
        if not self.converted_to_order:
            from orders.models import ProjectOrder
            order = ProjectOrder.objects.create(
                user=user,
                package=self.package,
                project_type=self.contact.message[:100],
                description=self.contact.message,
                total_amount=self.package.base_price,
                status='inquiry'
            )
            self.converted_to_order = True
            self.converted_at = timezone.now()
            self.save()
            return order
        return None