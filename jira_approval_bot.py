#!/usr/bin/env python3
"""
Jira Ticket Approval Automation Script
This script provides a chat interface to approve Jira tickets with user confirmation.
"""

import sys
from jira import JIRA
import getpass
from datetime import datetime

class JiraApprovalBot:
    def __init__(self):
        self.jira = None
        self.server = None
        self.username = None
        
    def connect_to_jira(self):
        """Establish connection to Jira server"""
        print("=== Jira Connection Setup ===")
        
        # # Get Jira server details
        # self.server = input("Enter your Jira server URL (e.g., https://yourcompany.atlassian.net): ").strip()
        # self.username = input("Enter your Jira username/email: ").strip()
        
        # # Get password securely
        # password = getpass.getpass("Enter your Jira password/API token: ")

        self.server = "https://suprajareddybujji.atlassian.net"
        self.username = "kartik.bansal@publicissapient.com"
        
        # Get password securely
        password = getpass.getpass("Enter your Jira password/API token: ")
        
        try:
            # Connect to Jira
            self.jira = JIRA(server=self.server, basic_auth=(self.username, password))
            print(f"✅ Successfully connected to Jira as {self.username}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Jira: {str(e)}")
            return False
    
    def get_ticket_info(self, ticket_key):
        """Retrieve ticket information from Jira"""
        try:
            issue = self.jira.issue(ticket_key)

            print(f"**************** {issue.fields}")
            return {
                'key': issue.key,
                'summary': issue.fields.summary,
                'status': issue.fields.status.name,
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                'description': issue.fields.description or 'No description provided',
                'issue_object': issue
                # 'Addional_Information': issue.fields.Addional_Information.displayName or 'No description provided',
                # 'resource_name' : issue.fields.resource_name.displayName or 'No description provided',
                # 'gurdrail/policyControl' : issue.fields.gurdrail/policyControl.displayName or 'No description provided'
            }

        except Exception as e:
            print(f"❌ Error retrieving ticket {ticket_key}: {str(e)}")
            return None
    
    def display_ticket_info(self, ticket_info):
        """Display ticket information in a formatted way"""
        print("\n" + "="*60)
        print("📋 TICKET INFORMATION")
        print("="*60)
        print(f"Key:                        {ticket_info['key']}")
        print(f"Summary:                    {ticket_info['summary']}")
        print(f"Status:                     {ticket_info['status']}")
        print(f"Assignee:                   {ticket_info['assignee']}")
        print(f"Reporter:                   {ticket_info['reporter']}")
        print(f"Description:                {ticket_info['description'][:100]}{'...' if len(ticket_info['description']) > 100 else ''}")
        # print(f"fields:                     {ticket_info['fields']}")
        print(f"issue_object:       {ticket_info['issue_object']}")
        # print(f"resource_name:              {ticket_info['resource_name']}")
        # print(f"gurdrail/policyControl:     {ticket_info['gurdrail/policyControl']}")
        print("="*60)
    
    def get_available_transitions(self, issue):
        """Get available status transitions for the ticket"""
        try:
            transitions = self.jira.transitions(issue)
            return transitions
        except Exception as e:
            print(f"❌ Error getting transitions: {str(e)}")
            return []
    
    def add_comment(self, issue, comment_text):
        """Add a comment to the Jira ticket"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            full_comment = f"{comment_text}\n\n_Automated approval on {timestamp} by {self.username}_"
            
            self.jira.add_comment(issue, full_comment)
            print("✅ Comment added successfully")
            return True
        except Exception as e:
            print(f"❌ Error adding comment: {str(e)}")
            return False
    
    def transition_ticket(self, issue, transition_name):
        """Transition the ticket to a new status"""
        try:
            transitions = self.get_available_transitions(issue)
            
            # Find the transition by name (case-insensitive)
            target_transition = None
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    target_transition = transition
                    break
            
            if target_transition:
                self.jira.transition_issue(issue, target_transition['id'])
                print(f"✅ Ticket status changed to: {transition_name}")
                return True
            else:
                print(f"❌ Transition '{transition_name}' not available")
                print("Available transitions:")
                for t in transitions:
                    print(f"  - {t['name']}")
                return False
                
        except Exception as e:
            print(f"❌ Error transitioning ticket: {str(e)}")
            return False
    
    def approve_ticket(self, ticket_key):
        """Main approval workflow"""
        print(f"\n🔍 Processing ticket: {ticket_key}")
        
        # Get ticket information
        ticket_info = self.get_ticket_info(ticket_key)
        if not ticket_info:
            return False
        
        # Display ticket information
        self.display_ticket_info(ticket_info)
        
        # Ask for approval confirmation
        print(f"\n❓ Should I approve this ticket ({ticket_key})?")
        print("Current status:", ticket_info['status'])
        
        while True:
            response = input("Enter 'yes' to approve, 'no' to cancel: ").lower().strip()
            if response in ['yes', 'y']:
                break
            elif response in ['no', 'n']:
                print("❌ Approval cancelled by user")
                return False
            else:
                print("Please enter 'yes' or 'no'")
        
        # Add approval comment
        print("\n📝 Adding approval comment...")
        if not self.add_comment(ticket_info['issue_object'], "✅ APPROVED - Ticket has been reviewed and approved for processing."):
            return False
        
        # Show available transitions and let user choose
        transitions = self.get_available_transitions(ticket_info['issue_object'])
        if not transitions:
            print("❌ No transitions available for this ticket")
            return False
        
        print("\n🔄 Available status transitions:")
        for i, transition in enumerate(transitions, 1):
            print(f"{i}. {transition['name']}")
        
        # Default to looking for "Approved" transition
        approved_transition = None
        for transition in transitions:
            if 'approved' in transition['name'].lower():
                approved_transition = transition['name']
                break
        
        if approved_transition:
            print(f"\n🎯 Found 'Approved' transition: {approved_transition}")
            confirm = input(f"Move to '{approved_transition}' status? (yes/no): ").lower().strip()
            if confirm in ['yes', 'y']:
                return self.transition_ticket(ticket_info['issue_object'], approved_transition)
        
        # Manual transition selection
        print("\nSelect transition number (or press Enter to skip status change):")
        choice = input("Choice: ").strip()
        
        if choice:
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(transitions):
                    selected_transition = transitions[choice_idx]['name']
                    return self.transition_ticket(ticket_info['issue_object'], selected_transition)
                else:
                    print("❌ Invalid choice")
            except ValueError:
                print("❌ Please enter a valid number")
        
        print("✅ Approval comment added (status unchanged)")
        return True
    
    def run_chat_interface(self):
        """Main chat interface loop"""
        print("🤖 Jira Ticket Approval Bot")
        print("="*40)
        
        # Connect to Jira
        if not self.connect_to_jira():
            return
        
        print("\n💬 Chat Interface Started")
        print("Commands:")
        print("  - Enter a Jira ticket key (e.g., PROJ-123)")
        print("  - Type 'quit' or 'exit' to end")
        print("  - Type 'help' for this message")
        
        while True:
            try:
                print("\n" + "-"*40)
                user_input = input("🎫 Enter Jira ticket key: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Jira Approval Bot shutting down.")
                    break
                elif user_input.lower() == 'help':
                    print("\n📖 Help:")
                    print("  - Enter a ticket key like 'PROJ-123', 'ABC-456', etc.")
                    print("  - The bot will show ticket details and ask for approval")
                    print("  - Type 'quit' to exit")
                    continue
                
                # Validate ticket key format (basic validation)
                if '-' not in user_input or len(user_input) < 3:
                    print("❌ Invalid ticket key format. Expected format: PROJECT-NUMBER (e.g., PROJ-123)")
                    continue
                
                # Process the ticket
                self.approve_ticket(user_input.upper())
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted by user. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                continue

def main():
    """Main function"""
    try:
        bot = JiraApprovalBot()
        bot.run_chat_interface()
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Check if required library is installed
    try:
        import jira
    except ImportError:
        print("❌ Required library 'jira' not found.")
        print("Install it using: pip install jira")
        sys.exit(1)
    
    main()
