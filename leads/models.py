from django.db import models


class Campaign(models.Model):
    name = models.CharField(max_length=200)
    saas_description = models.TextField(help_text="What does your SaaS do?")
    target_audience = models.TextField(help_text="Who is your target audience?")
    ai_search_queries = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('rejected', 'Rejected'),
    ]
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='leads')
    name = models.CharField(max_length=200, blank=True)
    linkedin_url = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    ai_score = models.IntegerField(default=0, help_text="AI relevance score 0-100")
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.email or 'no email'}"
