from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Campaign, Lead
from .forms import CampaignForm
from .scraper import run_campaign_scrape


def dashboard(request):
    campaigns = Campaign.objects.prefetch_related('leads').order_by('-created_at')
    return render(request, 'leads/dashboard.html', {'campaigns': campaigns})


def create_campaign(request):
    form = CampaignForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        campaign = form.save()
        messages.success(request, f'Campaign "{campaign.name}" created. Run scrape to find leads.')
        return redirect('campaign_detail', pk=campaign.pk)
    return render(request, 'leads/campaign_form.html', {'form': form})


def campaign_detail(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    leads = campaign.leads.order_by('-ai_score')
    return render(request, 'leads/campaign_detail.html', {'campaign': campaign, 'leads': leads})


def run_scrape(request, pk):
    campaign = get_object_or_404(Campaign, pk=pk)
    if request.method == 'POST':
        try:
            scraped = run_campaign_scrape(campaign)
            created = 0
            for lead_data in scraped:
                _, is_new = Lead.objects.get_or_create(
                    campaign=campaign,
                    linkedin_url=lead_data['linkedin_url'],
                    defaults={
                        'name': lead_data['name'],
                        'email': lead_data['email'],
                        'title': lead_data['title'],
                        'company': lead_data['company'],
                        'ai_score': lead_data['ai_score'],
                    }
                )
                if is_new:
                    created += 1
            messages.success(request, f'Scrape complete! Found {created} new leads.')
        except Exception as e:
            messages.error(request, f'Scrape failed: {e}')
    return redirect('campaign_detail', pk=pk)


def update_lead_status(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.status = request.POST.get('status', lead.status)
        lead.save()
    return redirect('campaign_detail', pk=lead.campaign.pk)
