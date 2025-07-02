#!/usr/bin/env python3
"""
Test script for ConnectWise Ticket Assigner Azure Function
This script helps validate the API integration and test the function logic locally.
"""

import os
import sys
import json
import requests
import base64
from datetime import datetime
from typing import List, Dict

# Add the current directory to Python path to import the function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the function module
from __init__ import (
    get_connectwise_auth_headers,
    get_unassigned_tickets,
    get_available_techs,
    get_tech_workload,
    select_best_tech,
    assign_ticket_to_tech,
    add_assignment_note,
    TECH_ASSIGNMENT_RULES
)

def test_connectwise_connection():
    """Test basic ConnectWise API connectivity."""
    print("🔍 Testing ConnectWise API connection...")
    
    try:
        headers = get_connectwise_auth_headers()
        base_url = f"{os.environ.get('CONNECTWISE_SITE', 'https://api-na.myconnectwise.net')}/v4_6_release/apis/3.0/service/tickets"
        
        # Test with a simple query
        params = {'pageSize': 1}
        resp = requests.get(base_url, headers=headers, params=params, timeout=30)
        
        if resp.status_code == 200:
            print("✅ ConnectWise API connection successful")
            return True
        else:
            print(f"❌ ConnectWise API connection failed: {resp.status_code} - {resp.text}")
            return False
            
    except Exception as e:
        print(f"❌ ConnectWise API connection error: {e}")
        return False

def test_get_unassigned_tickets():
    """Test fetching unassigned tickets."""
    print("\n🔍 Testing unassigned tickets fetch...")
    
    try:
        tickets = get_unassigned_tickets()
        print(f"✅ Found {len(tickets)} unassigned tickets")
        
        if tickets:
            print("Sample tickets:")
            for i, ticket in enumerate(tickets[:3]):  # Show first 3
                print(f"  {i+1}. ID: {ticket.get('id')} - {ticket.get('summary', 'No summary')}")
                print(f"     Board: {ticket.get('board', {}).get('name', 'Unknown')}")
                print(f"     Priority: {ticket.get('priority', {}).get('name', 'Unknown')}")
                print(f"     Status: {ticket.get('status', {}).get('name', 'Unknown')}")
                print()
        
        return tickets
        
    except Exception as e:
        print(f"❌ Error fetching unassigned tickets: {e}")
        return []

def test_get_available_techs():
    """Test fetching available techs."""
    print("\n🔍 Testing available techs fetch...")
    
    try:
        techs = get_available_techs()
        print(f"✅ Found {len(techs)} available techs")
        
        if techs:
            print("Available techs:")
            for tech in techs:
                print(f"  - {tech.get('fullName', 'Unknown')} ({tech.get('emailAddress', 'No email')}) - ID: {tech.get('id')}")
        
        return techs
        
    except Exception as e:
        print(f"❌ Error fetching available techs: {e}")
        return []

def test_tech_workload():
    """Test tech workload calculation."""
    print("\n🔍 Testing tech workload calculation...")
    
    techs = get_available_techs()
    if not techs:
        print("❌ No techs available to test workload")
        return
    
    # Test workload for first few techs
    for tech in techs[:3]:
        tech_id = tech['id']
        tech_name = tech.get('fullName', tech.get('emailAddress', 'Unknown'))
        
        try:
            workload = get_tech_workload(tech_id)
            print(f"  {tech_name}: {workload} active tickets")
        except Exception as e:
            print(f"  ❌ Error getting workload for {tech_name}: {e}")

def test_tech_selection():
    """Test tech selection logic."""
    print("\n🔍 Testing tech selection logic...")
    
    tickets = get_unassigned_tickets()
    techs = get_available_techs()
    
    if not tickets or not techs:
        print("❌ Need both tickets and techs to test selection")
        return
    
    # Test selection for first few tickets
    for i, ticket in enumerate(tickets[:3]):
        print(f"\nTesting ticket {i+1}: {ticket.get('summary', 'No summary')}")
        
        try:
            best_tech = select_best_tech(ticket, techs)
            if best_tech:
                print(f"  ✅ Selected: {best_tech.get('fullName', 'Unknown')} ({best_tech.get('emailAddress', 'No email')})")
            else:
                print(f"  ❌ No suitable tech found")
        except Exception as e:
            print(f"  ❌ Error selecting tech: {e}")

def test_assignment_rules():
    """Test and display assignment rules configuration."""
    print("\n🔍 Testing assignment rules configuration...")
    
    print("Current assignment rules:")
    for board, rules in TECH_ASSIGNMENT_RULES.items():
        print(f"\n  Board: {board}")
        print(f"    Default techs: {rules.get('default_techs', [])}")
        
        priority_techs = rules.get('priority_techs', {})
        if priority_techs:
            print(f"    Priority techs:")
            for priority, techs in priority_techs.items():
                print(f"      {priority}: {techs}")
        else:
            print(f"    No priority-specific techs")

def simulate_assignment(ticket_id: int, tech_id: int, dry_run: bool = True):
    """Simulate ticket assignment (dry run by default)."""
    print(f"\n🔍 Simulating assignment of ticket {ticket_id} to tech {tech_id}...")
    
    if dry_run:
        print("  🚫 DRY RUN - No actual assignment will be made")
        return True
    
    try:
        # Get tech name for logging
        techs = get_available_techs()
        tech_name = "Unknown"
        for tech in techs:
            if tech['id'] == tech_id:
                tech_name = tech.get('fullName', tech.get('emailAddress', 'Unknown'))
                break
        
        # Attempt assignment
        success = assign_ticket_to_tech(ticket_id, tech_id)
        if success:
            print(f"  ✅ Successfully assigned ticket {ticket_id} to {tech_name}")
            
            # Add assignment note
            note_success = add_assignment_note(ticket_id, tech_name)
            if note_success:
                print(f"  ✅ Added assignment note to ticket {ticket_id}")
            else:
                print(f"  ⚠️  Failed to add assignment note to ticket {ticket_id}")
        else:
            print(f"  ❌ Failed to assign ticket {ticket_id} to {tech_name}")
        
        return success
        
    except Exception as e:
        print(f"  ❌ Error during assignment simulation: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 ConnectWise Ticket Assigner - Test Suite")
    print("=" * 50)
    
    # Check environment variables
    required_vars = [
        'CONNECTWISE_SITE',
        'CONNECTWISE_COMPANY_ID', 
        'CONNECTWISE_PUBLIC_KEY',
        'CONNECTWISE_PRIVATE_KEY',
        'CONNECTWISE_CLIENT_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your environment or local.settings.json")
        return
    
    # Run tests
    connection_ok = test_connectwise_connection()
    if not connection_ok:
        print("\n❌ Cannot proceed without ConnectWise connection")
        return
    
    test_assignment_rules()
    tickets = test_get_unassigned_tickets()
    techs = test_get_available_techs()
    test_tech_workload()
    test_tech_selection()
    
    # Interactive assignment test
    if tickets and techs:
        print("\n" + "=" * 50)
        print("🎯 Interactive Assignment Test")
        print("=" * 50)
        
        # Show available tickets
        print("\nAvailable unassigned tickets:")
        for i, ticket in enumerate(tickets[:5]):  # Show first 5
            print(f"{i+1}. ID: {ticket['id']} - {ticket.get('summary', 'No summary')}")
        
        # Show available techs
        print("\nAvailable techs:")
        for i, tech in enumerate(techs[:5]):  # Show first 5
            print(f"{i+1}. ID: {tech['id']} - {tech.get('fullName', 'Unknown')}")
        
        try:
            choice = input("\nEnter ticket number to test assignment (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return
            
            ticket_idx = int(choice) - 1
            if 0 <= ticket_idx < len(tickets):
                ticket = tickets[ticket_idx]
                
                # Select best tech for this ticket
                best_tech = select_best_tech(ticket, techs)
                if best_tech:
                    print(f"\nSelected tech: {best_tech.get('fullName', 'Unknown')} (ID: {best_tech['id']})")
                    
                    # Ask if user wants to actually assign
                    assign_choice = input("Do you want to actually assign this ticket? (y/N): ").strip().lower()
                    if assign_choice == 'y':
                        simulate_assignment(ticket['id'], best_tech['id'], dry_run=False)
                    else:
                        simulate_assignment(ticket['id'], best_tech['id'], dry_run=True)
                else:
                    print("❌ No suitable tech found for this ticket")
            else:
                print("❌ Invalid ticket number")
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Test completed")
    
    print("\n✅ Test suite completed!")

if __name__ == "__main__":
    main() 