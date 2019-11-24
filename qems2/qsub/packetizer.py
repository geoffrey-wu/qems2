__author__ = 'mbentley'

import re
import json
import random
import string

from datetime import datetime
from django.utils import timezone

from qems2.qsub.models import *
<<<<<<< HEAD
from qems2.qsub.utils import *
=======
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a
from qems2.qsub.model_utils import *

# TODO: Add tests
def create_acf_packet(qset, packet_name, created_by, regular_distribution, tiebreaker_distribution):
    packet = Packet.objects.create(question_set=qset, packet_name=packet_name, created_by=created_by, packet_type=ACF_PACKET)
    packet.save()
    create_period_recursive(question_set, ACF_REGULAR_PERIOD, regular_distribution, packet)
    create_period_recursive(question_set, ACF_TIEBREAKER_PERIOD, tiebreaker_distribution, packet)
    
# TODO: Add tests
def create_vhsl_packet(qset, tossup_distribution, bonus_distribution, tiebreaker_distribution):
    packet = Packet.objects.create(question_set=qset, packet_name=packet_name, created_by=created_by, packet_type=VHSL_PACKET)
    packet.save()
    create_period_recursive(question_set, VHSL_TOSSUP_PERIOD, tossup_distribution, packet)
    create_period_recursive(question_set, VHSL_BONUS_PERIOD, bonus_distribution, packet)
    create_period_recursive(question_set, VHSL_TIEBREAKER_PERIOD, tiebreaker_distribution, packet)
    
# Creates a new period, figures out if it needs to create a new period entry, populates
# PeriodWideCategoryEntries and OnePeriodCategoryEntries appropriately
# TODO: Add tests
def create_period_recursive(question_set, period_type, distribution, packet):
    pwe, created = PeriodWideEntry.objects.get_or_create(question_set=qset, period_type=period_type, distribution=distribution)
    pwe.period_count += 1
    pwe.save()
    
    if (created):
        create_period_wide_category_entries(pwe)
        
    period = Period.objects.create(name=period_type, packet=packet, period_wide_entry=pwe)        
    create_one_period_category_entries(pwe, period)    

# TODO: Add tests
def create_period_wide_category_entries(period_wide_entry):
    categories = CategoryEntry.objects.filter(distribution=period_wide_entry.distribution)
    for category in categories:
        pwce = PeriodWideCategoryEntry.objects.create(period_wide_entry=period_wide_entry, category_entry=category)
        pwce.save()

# TODO: Add tests
def create_one_period_category_entries(period_wide_entry, period):
    period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=period_wide_entry)
    for pwce in period_wide_category_entry:
        opce = OnePeriodCategoryEntry.objects.create(period=period, period_wide_category_entry=pwce)
        opce.save()

# TODO: Add tests
def set_packet_requirements(qset):
    clear_questions(qset)
    reset_category_counts(qset, True)
    
    # double check the assumptions here
    packets = Packet.objects.filter(question_set=qset)
    packet_count = len(packets)
                
    for pwe in PeriodWideEntry.objects.filter(question_set=qset):
        # Set the totals at the pwe level
        pwe.acf_tossup_total = pwe.distribution.acf_tossup_per_period_count * packet_count
        pwe.acf_bonus_total = pwe.distribution.acf_bonus_per_period_count * packet_count
        pwe.vhsl_bonus_total = pwe.distribution.vhsl_bonus_per_period_count * packet_count
        pwe.save()
        
        # Now we need to set the total for each pwce
        # We start by setting the integer, then we randomly decide to bring in fractions
                
        # We know that each attribute of a distribution from subsub to sub to category to period will add up
        # We will build down from the highest level (category)
        # If there are fractions we need to aggregate the fractions from everything else at this level and
        # in a random but weighted way pick what to bring over
        
        # Get the top-level categories from the set and calculate how many questions to give them
        pwce_top_level = PeriodWideCategoryEntry.objects.filter(period_wide_entry=pwe, category_entry_for_distribution__category_entry__category_type=CATEGORY)        
        assign_pwce(pwce_top_level, packet_count, pwe.acf_tossup_total, pwe.acf_bonus_total, pwe.vhsl_bonus_total)

        # Do the same for each sub category      
        sub_children = []     
           
        for parent in pwce_top_level:
            all_children = get_children_from_period_wide_category_entry(parent)
            for pwce in children:
                if (pwce.get_category_type == SUB_CATEGORY):
                    sub_children.append(pwce)
            
            assign_pwce(sub_children, packet_count, parent.acf_tossup_total_across_periods, parent.acf_bonus_total_across_periods, parent.vhsl_bonus_total_across_periods)
                        
        # And for each subsubcategory
        sub_sub_children = []
        for parent in sub_children:
            all_children = get_children_from_period_wide_category_entry(parent)
            for pwce in children:
                if (pwce.get_category_type == SUB_SUB_CATEGORY):
                    sub_children.append(pwce)
                    
            assign_pwce(sub_sub_children, packet_count, parent.acf_tossup_total_across_periods, parent.acf_bonus_total_across_periods, parent.vhsl_bonus_total_across_periods)
     
        
# TODO: Add tests
# set the total questions to be an integer, and then store the fractions for random selection
def assign_pwce(pwce_list, packet_count, total_acf_tossup, total_acf_bonus, total_vhsl_bonus):
    cur_acf_tossup_count = 0
    cur_acf_bonus_count = 0
    cur_vhsl_bonus_count = 0
    
    acf_tossup_fractions = []
    acf_bonus_fractions = []
    vhsl_bonus_fractions = []
    
    for pwce in pwce_list:            
        pwce.acf_tossup_total_across_periods = int(pwce.category_entry_for_distribution.acf_tossup_fraction * packet_count)
        cur_acf_tossup_count += pwce.acf_tossup_total_across_periods            
        acf_tossup_fractions = get_fraction_array(pwce, pwce.acf_tossup_total_across_periods)
                    
        pwce.acf_bonus_total_across_periods = int(pwce.category_entry_for_distribution.acf_bonus_fraction * packet_count)
        cur_acf_bonus_count += pwce.acf_bonus_total_across_periods                        
        acf_bonus_fractions = get_fraction_array(pwce, pwce.acf_bonus_total_across_periods)

        pwce.vhsl_bonus_total_across_periods = int(pwce.category_entry_for_distribution.vhsl_bonus_fraction * packet_count)
        cur_vhsl_bonus_count += pwce.vhsl_bonus_total_across_periods            
        vhsl_bonus_fractions = get_fraction_array(pwce, pwce.vhsl_bonus_total_across_periods)
        
        pwce.save()
    
    get_pwce_from_fractions(acf_tossup_fractions, ACF_STYLE_TOSSUP, total_acf_tossup - cur_acf_tossup_count)        
    get_pwce_from_fractions(acf_bonus_fractions, ACF_STYLE_BONUS, total_acf_bonus - cur_acf_bonus_count)
    get_pwce_from_fractions(vhsl_bonus_fractions, VHSL_BONUS, total_vhsl_bonus - cur_vhsl_bonus_count)    
    
def get_fraction_array(pwce, value):
    fractions = []
    fraction = round(round(value - int(value), 4) * 1000, 0)
    print "Fraction before rounding: " + str(fraction)
    fraction = int(fraction)
    print "Fraction after rounding: " + str(fraction)
    for i in range(0, fraction):
        fractions.append(pwce)
    
    return fractions    

# TODO: Add tests        
def get_pwce_from_fractions(fractions, question_type, items_to_process, seed=-1):
    if (seed != -1):
        random.seed(seed)
    else:
        random.seed()
    
    pwce_list = []
    cur_items_processed = 0
    
    # Break fraction ties based on probability
    while (cur_items_processed < items_to_process and len(fractions) > 0):
        index = random.randint(0, len(fractions) - 1)
        pwce = fractions[index]
        
        cur_items_processed += 1
        
        if (question_type == ACF_STYLE_TOSSUP):
            pwce.acf_tossup_total_across_periods += 1
            pwce.save()
        elif (question_type == ACF_STYLE_BONUS):
            pwce.acf_bonus_total_across_periods += 1
            pwce.save()
        elif (question_type == VHSL_BONUS):
            pwce.vhsl_bonus_total_across_periods += 1
            pwce.save()
                    
        # Remove this from the list of eligible categories to choose from
        for i in range(len(fractions) - 1, 0):
            if (fractions[i] == pwce):
                fractions.pop(i)
                
    return pwce_list

# Determines if you've written enough questions to start packetization
# TODO: Finish implementing
# TODO: Add tests
def is_question_set_complete(qset):
    # Get every period-wide entry, see if requirement is satisfied
    all_periods_dict, per_period_dict = get_per_category_requirements_for_set(qset)
    for cat in all_periods_dict:
        req = all_periods_dict[cat]
        
        
        
        if (not req.is_requirement_satisfied()):
            return False
    
    return True

# Returns a dictionary of requirements for all
# items in the set (spanning across periods).
# So, for instance, if there are multiple periods with
# History - European needed, gets the total for that category
# TODO: Add tests
def get_per_category_requirements_for_set(qset):    
    all_periods_dict = {} # Category Name to DistributionRequirement mapping
    period_wide_entries = PeriodWideEntry.objects.filter(question_set=qset)
    for pwe in period_wide_entries:
        period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=pwe)
        for pwce in period_wide_category_entries:
            
            # If we haven't seen this category entry before, find all of the 
            # current questions written in this category entry in the set
            if (not str(pwce.category_entry_for_distribution) in all_periods_dict):
                req = get_questions_written_across_periods_for_category(qset, pwce)
                all_periods_dict[str(pwce.category_entry_for_distribution)] = req
                
            # For all pwce's, add to how many questions they need
            req = all_periods_dict[str(pwce.category_entry_for_distribution)]            
            req.acf_tossups_needed += pwce.acf_tossup_total_across_periods
            req.acf_bonuses_needed += pwce.acf_bonus_total_across_periods
            req.vhsl_bonuses_needed += pwce.vhsl_bonus_total_across_periods
            all_periods_dict[str(req)] = req
            
    return all_periods_dict
    
# Determines how many total questions in this category have already been written in this set
def get_questions_written_across_periods_for_category(qset, pwce):
    # Calculate how many we've already written in this category from the set                
    # At the category level, I want to sum up anything that just matches my category name
    cefd = pwce.category_entry_for_distribution
    c = cefd.category_entry
    req = DistributionRequirement(c)
    if (c.category_type == CATEGORY):
        # Return anything that matches category (implies sub and subsub match)
        req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_TOSSUP), category_entry__category_name=c.category_name))
        req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_BONUS), category_entry__category_name=c.category_name))
        req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(VHSL_BONUS), category_entry__category_name=c.category_name))
    elif (c.category_type == SUB_CATEGORY):
        # Return anything that matches category and sub (implies subsub match)
        req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_TOSSUP), category_entry__category_name=c.category_name, category_entry__sub_category_name=c.sub_category_name))                    
        req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_BONUS), category_entry__category_name=c.category_name, category_entry__sub_category_name=c.sub_category_name))                    
        req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(VHSL_BONUS), category_entry__category_name=c.category_name, category_entry__sub_category_name=c.sub_category_name))                    
    else:
        # Just match on exact category--won't match subcategory because of the if statement
        req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_TOSSUP), category=c))
        req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(ACF_STYLE_BONUS), category=c))
        req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type=get_question_type_from_string(VHSL_BONUS), category=c))
        
    return req
    
    
# Goes through the set and creates placeholder questions to enable to you to do packetization
# You will repalce these questions later
# TODO: Add tests
def fill_unassigned_questions(qset, author):
    # Get every period-wide entry, see if requirement is satisfied
    all_periods_dict = get_per_category_requirements_for_set(qset)
    for cat in all_periods_dict:
        req = all_periods_dict[cat]
        if (not req.is_requirement_satisfied()):
            # Now we need to add the appropriate number of questions
            # but we only really want to do this at the lowest level -- i.e. don't add
            # a question of category History and then another one of History - American                        
            children = get_children_from_category_entry(req.category_entry)
            
            # If there's just 1 child, it means that we satisfy this set's needs by adding at this level
            if (len(children) == 1):
                difference = req.acf_tossups_needed - req.acf_tossups_written
                for i in range(0, difference):
                    tossup = Tossup.objects.create(
                        question_set=qset,
                        tossup_text="Placeholder Question for " + str(cat),
                        tossup_answer = "_Placeholder Answer_",
                        author=author,
                        question_type = get_question_type_from_string(ACF_STYLE_TOSSUP), 
                        location = "",
                        time_period = "",
                        created_date=timezone.now(),
                        last_changed_date=timezone.now(),
                        category_entry=req.category_entry)
                    tossup.save_question(QUESTION_CREATE, author)
                    
                difference = req.acf_bonuses_needed - req.acf_bonuses_written
                for i in range(0, difference):
                    bonus = Bonus.objects.create(
                        question_set=qset, 
                        leadin="Placeholder Question for " + str(cat),
                        part1_text = "Placeholder question", 
                        part1_answer = "_Placeholder Answer_",
                        part2_text = "Placeholder question", 
                        part2_answer = "_Placeholder Answer_", 
                        part3_text = "Placeholder question", 
                        part3_answer = "_Placeholder Answer_",                 
                        author=author, 
                        question_type = "ACF-style bonus", 
                        location = "", 
                        time_period = "",
                        created_date=timezone.now(),
                        last_changed_date=timezone.now(),
                        category_entry=req.category_entry)
                    bonus.save_question(QUESTION_CREATE, author)

                difference = req.acf_tossups_needed - req.acf_tossups_written
                for i in range(0, difference):
                    bonus = Bonus.objects.create(
                        question_set=qset, 
                        leadin="",
                        part1_text = "Placeholder Question for " + str(cat), 
                        part1_answer = "_Placeholder Answer_",
                        part2_text = "", 
                        part2_answer = "",
                        part3_text = "", 
                        part3_answer = "",                   
                        author=author, 
                        question_type = "ACF-style bonus", 
                        location = "", 
                        time_period = "",
                        created_date=timezone.now(),
                        last_changed_date=timezone.now(),
                        category_entry=req.category_entry)
                    bonus.save_question(QUESTION_CREATE, author)

# TODO: Add tests
def packetize(qset):
    if (not is_question_set_complete(qset)):
        print "Not enough questions in the set"
        return
    
    clear_questions(qset)
    reset_category_counts(qsets)
    
    packets = Packet.objects.filter(question_set=qset)
    for packet in packets:
        periods = Period.objects.filter(packet=packet)
        for period in periods:            
            distribution = Distribution.objects.get(distribution=period.period_wide_entry.distribution)
            
            assign_acf_tossups_to_period(qset, period, distribution)
            assign_acf_bonuses_to_period(qset, period, distribution)
            assign_vhsl_bonuses_to_period(qset, period, distribution)
            
            randomize_acf_tossups_in_period(qset, period)
            randomize_acf_bonuses_in_period(qset, period)
            randomize_vhsl_bonuses_in_period(qset, period)            
            
# TODO: Add tests
def randomize_acf_tossups_in_period(qset, period):
    tossups = get_assigned_acf_tossups_in_period(qset, period)
    
    # This is a naive algorithm that looks for best entropy between categories
    bestQuestionOrder = []
    bestDistance = 0
    for s in range(0, 50):
        curDistance = 0
        shuffle(tossups)
        last_seen = {}
        index = 0
        for tossup in tossups:
            top_level_cat = tossup.category_entry.category_name
            if (top_level_cat in last_seen):
                curDistance += (index - last_seen[top_level_cat])
            last_seen[top_level_cat] = index            
            index += 1
        if (curDistance > bestDistance):
            bestQuestionOrder = tossups
            print "Best question distance: " + str(bestDistance)
            print "Set best question order: " + str(tossups)
    
    # Now that we have an order, set it
    index = 1
    for tossup in bestQuestionOrder:
        tossup.question_number = index
        tossup.save()
        index += 1    

# TODO: Add tests
def randomize_acf_bonuses_in_period(qset, period):
    bonuses = get_assigned_acf_bonuses_in_period(qset, period)
    randomize_bonuses_in_period(bonuses)
    
# TODO: Add tests
def randomize_vhsl_bonuses_in_period(qset, period):
    bonuses = get_assigned_vhsl_bonuses_in_period(qset, period)
    randomize_bonuses_in_period(bonuses)
   
# TODO: Reduce code duplication
def randomize_bonuses_in_period(bonuses):    
    # This is a naive algorithm that looks for best entropy between categories
    bestQuestionOrder = []
    bestDistance = 0
    for s in range(0, 50):
        curDistance = 0
        shuffle(bonuses)
        last_seen = {}
        index = 0
        for bonus in bonuses:
            top_level_cat = bonus.category_entry.category_name
            if (top_level_cat in last_seen):
                curDistance += (index - last_seen[top_level_cat])
            last_seen[top_level_cat] = index            
            index += 1
        if (curDistance > bestDistance):
            bestQuestionOrder = bonuses
            print "Best question distance: " + str(bestDistance)
            print "Set best question order: " + str(bonuses)
    
    # Now that we have an order, set it
    index = 1
    for bonus in bestQuestionOrder:
        bonus.question_number = index
        bonus.save()
        index += 1   

# TODO: Add tests
# TODO: Let you pass a seed
def assign_acf_tossups_to_period(qset, period, distribution):
    acf_tossups = get_unassigned_acf_tossups(qset)    
    while (period.acf_tossup_cur < distribution.acf_tossup_per_packet_count):
        index = randint(0, len(acf_tossups) - 1)
        acf_tossup = acf_tossups[index]
        acf_tossups.remove(acf_tossup)
        if (is_acf_tossup_valid_in_period(qset, period, acf_tossup)):
            acf_tossup.packet = packet
            acf_tossup.period = period
            acf_tossup.save()
            period.acf_tossup_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category_entry, period)
            if (c_pwce is not None):
                c_pwce.acf_tossup_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.acf_tossup_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.acf_tossup_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.acf_tossup_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.acf_tossup_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.acf_tossup_cur_in_period += 1
                ssc_opce.save()

# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def assign_acf_bonuses_to_period(qset, period, distribution):
    acf_bonuses = get_unassigned_acf_bonuses(qset)
    
    while (period.acf_bonus_cur < distribution.acf_bonus_per_packet_count):
        index = randint(0, len(acf_bonuses) - 1)
        acf_bonus = acf_bonuses[index]
        acf_bonuses.remove(acf_bonus)
        if (is_acf_bonus_valid_in_period(qset, period, acf_bonus)):
            acf_bonus.packet = packet
            acf_bonus.period = period
            acf_bonus.save()
            period.acf_bonus_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category_entry, period)
            if (c_pwce is not None):
                c_pwce.acf_bonus_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.acf_bonus_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.acf_bonus_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.acf_bonus_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.acf_bonus_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.acf_bonus_cur_in_period += 1
                ssc_opce.save() 
                        
# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def assign_vhsl_bonuses_to_period(qset, period, distribution):
    vhsl_bonuses = get_unassigned_vhsl_bonuses(qset)    
    
    while (period.vhsl_bonus_cur < distribution.vhsl_bonus_per_packet_count):
        index = randint(0, len(vhsl_bonuses) - 1)
        vhsl_bonus = vhsl_bonuses[index]
        vhsl_bonuses.remove(vhsl_bonus)
        if (is_vhsl_bonus_valid_in_period(qset, period, vhsl_bonus)):
            vhsl_bonus.packet = packet
            vhsl_bonus.period = period
            vhsl_bonus.save()
            period.vhsl_bonus_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category_entry, period)
            if (c_pwce is not None):
                c_pwce.vhsl_bonus_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.vhsl_bonus_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.vhsl_bonus_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.vhsl_bonus_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.vhsl_bonus_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.vhsl_bonus_cur_in_period += 1
                ssc_opce.save()  

# A category entry might be a sub-sub or sub category meaning that it has
# 1 or 2 parent categories.  This method returns the whole set
def get_parents_from_category_entry(category_entry):
    if (category_entry.category_type == CATEGORY):
        return category_entry, None, None
<<<<<<< HEAD
    elif (category_entry.category_type == SUB_CATEGORY):
        category = None
        try:
            category = CategoryEntry.objects.get(category_name=category_entry.category_name, category_type=CATEGORY)
        except Exception as ex:
            print "Could not find parent for: " + str(category_entry)
        
        return category, category_entry, None
    else:
        category = None
        try:
            category = CategoryEntry.objects.get(category_name=category_entry.category_name, category_type=CATEGORY)
        except Exception as ex:
            print "Could not find parent for: " + str(category_entry)
        
        sub_category = None
        try:
            sub_category = CategoryEntry.objects.get(category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name, category_type=SUB_CATEGORY)
        except Exception as ex:
            print "Could not find parent for: " + str(category_entry)
                
=======

    category_query = CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=None)
    category = None if (not category_query.exists()) else category_query[0]
    if (category_entry.sub_sub_category_name is None or category_entry.sub_sub_category_name == ''):
        return category, category_entry, None
    else:
        sub_category_query = CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name, sub_sub_category_name=None)
        sub_category = None if (not sub_category_query.exists()) else sub_category_query[0]
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a
        return category, sub_category, category_entry

# Gets the current entry and any children of this category.  For instance,
# "History" could return "History" and "History - European" and
# "History - European - British"
def get_children_from_category_entry(category_entry):
<<<<<<< HEAD
    children = []
    if (category_entry.category_type == CATEGORY):
        children = CategoryEntry.objects.filter(category_name=category_entry.category_name)
    elif (category_entry.category_type==SUB_CATEGORY):
        children = CategoryEntry.objects.filter(category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name)
=======
    if (category_entry.sub_category_name is None or category_entry.sub_category_name == ''):
        return CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name)
    elif (category_entry.sub_sub_category_name is None or category_entry.sub_sub_category_name == ''):
        return CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name)
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a
    else:
        # subsub categories don't have children
        return [category_entry]

def get_parents_from_category_entry_for_distribution(cefd):
    category_entry = cefd.category_entry
    ce_cat, ce_subcat, ce_subsubcat = get_parents_from_category_entry(category_entry)
    cat = None
    subcat = None
    subsubcat = None
    
    if (ce_cat is not None):
        cat = CategoryEntryForDistribution.objects.get(distribution=cefd.distribution, category_entry=ce_cat)

    if (ce_subcat is not None):
        subcat = CategoryEntryForDistribution.objects.get(distribution=cefd.distribution, category_entry=ce_subcat)

    if (ce_subsubcat is not None):
        subsubcat = CategoryEntryForDistribution.objects.get(distribution=cefd.distribution, category_entry=ce_subsubcat)
                
    return cat, subcat, subsubcat
    
def get_children_from_category_entry_for_distribution(cefd):
    children = []
    category_entry = cefd.category_entry
    ce_children = get_children_from_category_entry(category_entry)
    for ce_child in ce_children:
        children.append(CategoryEntryForDistribution.objects.get(distribution=cefd.distribution, category_entry=ce_child))
    
    return children     

def get_parents_from_period_wide_category_entry(pwce):
    cefd = pwce.category_entry_for_distribution
    cefd_cat, cefd_subcat, cefd_subsubcat = get_parents_from_category_entry_for_distribution(cefd)
    cat = None
    subcat = None
    subsubcat = None
    if (cefd_cat is not None):
        cat = PeriodWideCategoryEntry.objects.get(period_wide_entry=pwce.period_wide_entry, category_entry_for_distribution=cefd_cat)

    if (cefd_subcat is not None):
        subcat = PeriodWideCategoryEntry.objects.get(period_wide_entry=pwce.period_wide_entry, category_entry_for_distribution=cefd_subcat)

    if (cefd_subsubcat is not None):
        subsubcat = PeriodWideCategoryEntry.objects.get(period_wide_entry=pwce.period_wide_entry, category_entry_for_distribution=cefd_subsubcat)
        
    return cat, subcat, subsubcat
    
def get_children_from_period_wide_category_entry(pwce):
    children = []
    cefd = pwce.category_entry_for_distribution
    cefd_children = get_children_from_category_entry_for_distribution(cefd)
    for cefd_child in cefd_children:
        children.append(PeriodWideCategoryEntry.objects.get(period_wide_entry=pwce.period_wide_entry, category_entry_for_distribution=cefd_child))
    
    return children

def get_period_entries_from_category_entry_with_parents(category_entry, period):
    c, sc, ssc = get_parents_from_category_entry(category_entry)
    c_pwce, c_opce = get_period_entries_from_category_entry(c, period)
    sc_pwce, sc_opce = get_period_entries_from_category_entry(sc, period)
    ssc_pwce, ssc_opce = get_period_entries_from_category_entry(ssc, period)
    return c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce

def get_period_entries_from_category_entry(category_entry, period):   
    dist = period.period_wide_entry.distribution
    
    cefd = CategoryEntryForDistribution.objects.get(distribution=dist, category_entry=category_entry)
    pwce = PeriodWideCategoryEntry.objects.get(period_wide_entry=period.period_wide_entry, category_entry_for_distribution=cefd)
    opce = OnePeriodCategoryEntry.objects.get(period=period, period_wide_category_entry=pwce)
    return pwce, opce

# Make sure that we're under the limit period-wide and for just this period for all category combinations
# TODO: Add tests
def is_acf_tossup_valid_in_period(qset, period, tossup):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category_entry, period)
    
    if (c_pwce is not None and c_pwce.acf_tossup_cur_across_periods >= c_pwce.acf_tossup_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.is_over_min_acf_tossup_limit()):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.acf_tossup_cur_across_periods >= sc_pwce.acf_tossup_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.is_over_min_acf_tossup_limit()):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.acf_tossup_cur_across_periods >= ssc_pwce.acf_tossup_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.is_over_min_acf_tossup_limit()):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True

# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def is_acf_bonus_valid_in_period(qset, period, bonus):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(bonus.category_entry, period)
    
    if (c_pwce is not None and c_pwce.acf_bonus_cur_across_periods >= c_pwce.acf_bonus_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.is_over_min_acf_bonus_limit()):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.acf_bonus_cur_across_periods >= sc_pwce.acf_bonus_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.is_over_min_acf_bonus_limit()):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.acf_bonus_cur_across_periods >= ssc_pwce.acf_bonus_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.is_over_min_acf_bonus_limit()):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True
    
# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def is_vhsl_bonus_valid_in_period(qset, period, bonus):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(bonus.category_entry, period)
    
    if (c_pwce is not None and c_pwce.vhsl_bonus_cur_across_periods >= c_pwce.vhsl_bonus_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.is_over_min_vhsl_bonus_limit()):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.vhsl_bonus_cur_across_periods >= sc_pwce.vhsl_bonus_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.is_over_min_vhsl_bonus_limit()):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.vhsl_bonus_cur_across_periods >= ssc_pwce.vhsl_bonus_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.is_over_min_vhsl_bonus_limit()):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True
    
def get_question_count_for_category_in_period(qset, period, category):
    tossups = Tossup.objects.filter(question_set=qset, period=period, category_entry=category)
    bonuses = Bonus.objects.filter(question_set=qset, period=period, category_entry=category)
    return len(tossups) + len(bonuses)

def get_unassigned_acf_tossups(qset):
    acf_tossups = Tossup.objects.filter(question_set=qset, packet=None)
    return acf_tossups
    
def get_unassigned_acf_bonuses(qset):
<<<<<<< HEAD
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type__question_type=ACF_STYLE_BONUS, packet=None)
    return acf_bonuses
    
def get_unassigned_vhsl_bonuses(qset):
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type__question_type=VHSL_BONUS, packet=None)
=======
    question_type = get_question_type_from_string("ACF-style bonus")
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, packet=None)
    return acf_bonuses
    
def get_unassigned_vhsl_bonuses(qset):
    question_type = get_question_type_from_string("VHSL bonus")
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, packet=None)
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a
    return vhsl_bonuses
    
def get_assigned_acf_tossups_in_period(qset, period):
    acf_tossups = Tossup.objects.filter(question_set=qset, period=period)
    
    print "Found Tossup Count: " + str(len(acf_tossups))
    print "All tossups:"
    for tossup in Tossup.objects.filter(question_set=qset):
        print "Tossup: " + str(tossup)
    
    return acf_tossups
    
def get_assigned_acf_bonuses_in_period(qset, period):
<<<<<<< HEAD
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type__question_type=ACF_STYLE_BONUS, period=period)
    return acf_bonuses

def get_assigned_vhsl_bonuses_in_period(qset, period):
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type__question_type=VHSL_BONUS, period=period)
=======
    question_type = get_question_type_from_string("ACF-style bonus")
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, period=period)
    return acf_bonuses

def get_assigned_vhsl_bonuses_in_period(qset, period):
    question_type = get_question_type_from_string("VHSL bonus")
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, period=period)
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a
    return vhsl_bonuses

# Clear packet information from each question
def clear_questions(qset):
    print "Start clear_questions"
    
    tossups = Tossup.objects.filter(question_set=qset)
    for tossup in tossups:
        print "Clearing tossup: " + str(tossup)
        tossup.packet = None
        tossup.period = None
        tossup.question_number = None
        tossup.save()
    
    bonuses = Bonus.objects.filter(question_set=qset)
    for bonus in bonuses:
        print "Clearing bonus: " + str(bonus)
        bonus.packet = None
        bonus.period = None
        bonus.question_number = None
        bonus.save()
        
def reset_category_counts(qset, reset_totals=False):
    period_wide_entries = PeriodWideEntry.objects.filter(question_set=qset)
    for pwe in period_wide_entries:
        print "Reset pwe: " + str(pwe)
        pwe.reset_current_values()
        if (reset_totals):
            pwe.reset_total_values()
        pwe.save()
        
        periods = Period.objects.filter(period_wide_entry=pwe)
        for period in periods:
            print "Reset period: " + str(period)
            period.reset_current_values()
            period.save()
        
        period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=pwe)        
        for pwce in period_wide_category_entries:
            print "Reset pwce: " + str(pwce)
            pwce.reset_current_values()
            if (reset_totals):
                pwce.reset_total_values()
            pwce.save()
            
            one_period_category_entries = OnePeriodCategoryEntry.objects.filter(period_wide_category_entry=pwce)
            for opce in one_period_category_entries:
                print "Reset opce: " + str(opce)
                opce.reset_current_values()
<<<<<<< HEAD
=======
                if (reset_totals):
                    opce.reset_total_values()
                opce.save()
>>>>>>> dc5f333216071c2f7e80ec9a556251516d74364a

class DistributionRequirement():
    acf_tossups_written = 0
    acf_tossups_needed = 0
    acf_bonuses_written = 0
    acf_bonuses_needed = 0
    vhsl_bonuses_written = 0
    vhsl_bonuses_needed = 0
    category_entry = None
    period_name = ''
    
    def __init__(self, category_entry):
        self.category_entry = category_entry
    
    def __str__(self):
        return str(self.category_entry)
    
    def is_requirement_satisfied(self):
        if (self.acf_tossups_written < self.acf_tossups_needed):
            return False
            
        if (self.acf_bonuses_written < self.acf_bonuses_needed):
            return False
            
        if (self.vhsl_bonuses_writen < self.vhsl_bonuses_needed):
            return False
            
        return True
