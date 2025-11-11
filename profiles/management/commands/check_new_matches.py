from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from profiles.models import SavedSearch, Profile, Skill, NewMatchNotification  # ✅ Changed


class Command(BaseCommand):
    help = 'Check saved searches for new matches and create notifications'

    def handle(self, *args, **options):
        # Get all saved searches with notifications enabled
        saved_searches = SavedSearch.objects.filter(notify_on_new_matches=True)
        
        total_notifications = 0
        
        for search in saved_searches:
            self.stdout.write(f"Checking search: {search.name} (ID: {search.pk})")
            
            # Run the search
            criteria = search.search_criteria
            
            profiles = Profile.objects.filter(
                visibility='public',
                user__user_type='job_seeker'
            ).select_related('user').prefetch_related('skills')
            
            # Apply all filters
            if criteria.get('keywords'):
                keywords = str(criteria['keywords']).strip()
                if keywords:
                    profiles = profiles.filter(
                        Q(headline__icontains=keywords) |
                        Q(bio__icontains=keywords) |
                        Q(current_position__icontains=keywords)
                    )
            
            if criteria.get('location'):
                location = str(criteria['location']).strip()
                if location:
                    profiles = profiles.filter(location__icontains=location)
            
            if criteria.get('min_experience'):
                try:
                    min_exp = criteria['min_experience']
                    if isinstance(min_exp, str):
                        min_exp = min_exp.strip()
                        if min_exp:
                            min_exp = int(min_exp)
                            profiles = profiles.filter(years_experience__gte=min_exp)
                    elif isinstance(min_exp, (int, float)):
                        profiles = profiles.filter(years_experience__gte=int(min_exp))
                except (ValueError, TypeError):
                    pass
            
            if criteria.get('open_to_work') in ['on', 'true', True]:
                profiles = profiles.filter(open_to_work=True)
            
            if criteria.get('education_keyword'):
                edu = str(criteria['education_keyword']).strip()
                if edu:
                    profiles = profiles.filter(education__icontains=edu)
            
            if criteria.get('certification_keyword'):
                cert = str(criteria['certification_keyword']).strip()
                if cert:
                    profiles = profiles.filter(certifications__icontains=cert)
            
            if criteria.get('skill_ids'):
                try:
                    skill_ids = criteria['skill_ids']
                    if isinstance(skill_ids, str):
                        skill_ids = [int(sid) for sid in skill_ids.split(',') if sid.strip()]
                    elif isinstance(skill_ids, list):
                        skill_ids = [int(sid) for sid in skill_ids if sid]
                    
                    if skill_ids:
                        profiles = profiles.annotate(
                            skill_match_count=Count('skills', filter=Q(skills__id__in=skill_ids))
                        ).filter(skill_match_count__gt=0)
                except (ValueError, TypeError):
                    pass
            
            # Count current matches
            current_count = profiles.count()
            previous_count = search.last_match_count
            
            self.stdout.write(f"  Previous: {previous_count}, Current: {current_count}")
            
            # Check if there are new matches
            if current_count > previous_count:
                new_matches = current_count - previous_count
                
                # Create notification
                NewMatchNotification.create_new_match_notification(  # ✅ Changed
                    recruiter=search.recruiter,
                    saved_search=search,
                    new_count=new_matches,
                    total_count=current_count
                )
                
                total_notifications += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ Created notification for {search.recruiter.username}: {new_matches} new match(es)'
                    )
                )
            else:
                self.stdout.write(f'  No new matches')
            
            # Update search stats
            search.last_match_count = current_count
            search.last_run_at = timezone.now()
            search.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Check complete! Created {total_notifications} notification(s).'
            )
        )