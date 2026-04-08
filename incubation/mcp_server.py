"""
Customer Success FTE — MCP Server
==================================
Phase 1: Incubation

Model Context Protocol (MCP) server that exposes the customer success agent's
capabilities as tools. This allows other agents and systems to interact with
the FTE programmatically.

Tools exposed:
1. search_knowledge_base(query) -> relevant docs
2. create_ticket(customer_id, issue, priority, channel) -> ticket_id
3. get_customer_history(customer_id) -> past interactions across ALL channels
4. escalate_to_human(ticket_id, reason) -> escalation_id
5. send_response(ticket_id, message, channel) -> delivery_status
6. analyze_sentiment(message) -> sentiment score + confidence
"""

import json
import os
import sys
from typing import Optional
from enum import Enum
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from prototype import (
    CustomerSuccessAgent, SimpleKnowledgeBase, EscalationEngine,
    SimpleSentimentAnalyzer, ResponseFormatter, Channel, EscalationReason
)
from memory_manager import MemoryManager, ConversationStatus


# ─── MCP Server Implementation ─────────────────────────────────────────────

class MCPServer:
    """Simple MCP server implementation for the Customer Success FTE.
    
    Follows the MCP specification for tool definitions and execution.
    """

    def __init__(self, name: str = "customer-success-fte", docs_path: str = None):
        self.name = name
        self.version = "1.0.0"
        self.agent = CustomerSuccessAgent(kb_path=docs_path)
        self.memory = MemoryManager()
        self.tools = self._register_tools()

    def _register_tools(self) -> dict:
        """Register all available tools."""
        return {
            'search_knowledge_base': {
                'name': 'search_knowledge_base',
                'description': 'Search product documentation for relevant information. Use this when the customer asks questions about product features, how to use something, or needs technical information.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'The search query from the customer message'
                        },
                        'max_results': {
                            'type': 'integer',
                            'description': 'Maximum number of results to return (default: 5)',
                            'default': 5
                        },
                        'category': {
                            'type': 'string',
                            'description': 'Optional category filter (account, billing, technical, etc.)',
                            'enum': ['account', 'billing', 'technical', 'general', 'api', 'mobile', 'security', 'automation']
                        }
                    },
                    'required': ['query']
                },
                'handler': self._handle_search_kb
            },
            'create_ticket': {
                'name': 'create_ticket',
                'description': 'Create a support ticket for tracking customer interactions. ALWAYS create a ticket at the start of every conversation. Include the source channel for proper tracking.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'customer_id': {
                            'type': 'string',
                            'description': 'Unique customer identifier (email or auto-generated ID)'
                        },
                        'issue': {
                            'type': 'string',
                            'description': 'Description of the customer issue'
                        },
                        'priority': {
                            'type': 'string',
                            'description': 'Ticket priority level',
                            'enum': ['low', 'medium', 'high', 'urgent'],
                            'default': 'medium'
                        },
                        'channel': {
                            'type': 'string',
                            'description': 'Source channel of the inquiry',
                            'enum': ['email', 'whatsapp', 'web_form']
                        },
                        'category': {
                            'type': 'string',
                            'description': 'Issue category (general, technical, billing, feedback, bug_report)',
                            'default': 'general'
                        }
                    },
                    'required': ['customer_id', 'issue', 'channel']
                },
                'handler': self._handle_create_ticket
            },
            'get_customer_history': {
                'name': 'get_customer_history',
                'description': "Get customer's complete interaction history across ALL channels. Use this to understand context from previous conversations, even if they happened on a different channel.",
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'customer_id': {
                            'type': 'string',
                            'description': 'Unique customer identifier'
                        }
                    },
                    'required': ['customer_id']
                },
                'handler': self._handle_get_history
            },
            'escalate_to_human': {
                'name': 'escalate_to_human',
                'description': "Escalate conversation to human support. Use when: customer asks about pricing or refunds, customer sentiment is negative, you cannot find relevant information, or customer explicitly requests human help.",
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'ticket_id': {
                            'type': 'string',
                            'description': 'The ticket/conversation ID to escalate'
                        },
                        'reason': {
                            'type': 'string',
                            'description': 'Reason for escalation (pricing_inquiry, refund_request, legal_threat, angry_customer, human_requested, engineering_bug, compliance_question)',
                            'enum': ['pricing_inquiry', 'refund_request', 'legal_threat', 'angry_customer', 'human_requested', 'engineering_bug', 'compliance_question', 'enterprise_inquiry', 'cannot_answer']
                        },
                        'urgency': {
                            'type': 'string',
                            'description': 'Escalation urgency level',
                            'enum': ['P0', 'P1', 'P2', 'P3'],
                            'default': 'P2'
                        }
                    },
                    'required': ['ticket_id', 'reason']
                },
                'handler': self._handle_escalate
            },
            'send_response': {
                'name': 'send_response',
                'description': "Send response to customer via their preferred channel. The response will be automatically formatted for the channel. Email: formal with greeting/signature. WhatsApp: concise and conversational. Web: semi-formal.",
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'ticket_id': {
                            'type': 'string',
                            'description': 'The ticket/conversation ID'
                        },
                        'message': {
                            'type': 'string',
                            'description': 'The response message to send to the customer'
                        },
                        'channel': {
                            'type': 'string',
                            'description': 'Channel to send the response via',
                            'enum': ['email', 'whatsapp', 'web_form']
                        }
                    },
                    'required': ['ticket_id', 'message', 'channel']
                },
                'handler': self._handle_send_response
            },
            'analyze_sentiment': {
                'name': 'analyze_sentiment',
                'description': 'Analyze the sentiment of a customer message. Returns a score from 0.0 (very negative) to 1.0 (very positive). Use this to gauge customer satisfaction and determine if escalation is needed.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string',
                            'description': 'The customer message to analyze'
                        }
                    },
                    'required': ['message']
                },
                'handler': self._handle_sentiment
            },
            'identify_customer': {
                'name': 'identify_customer',
                'description': 'Identify or create a customer record from their identifiers (email, phone). Returns unified customer_id and basic profile. Use this on every incoming message.',
                'inputSchema': {
                    'type': 'object',
                    'properties': {
                        'email': {
                            'type': 'string',
                            'description': 'Customer email address'
                        },
                        'phone': {
                            'type': 'string',
                            'description': 'Customer phone number'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Customer name'
                        }
                    },
                    'required': []
                },
                'handler': self._handle_identify_customer
            }
        }

    # ─── Tool Handlers ───────────────────────────────────────────────────

    def _handle_search_kb(self, params: dict) -> str:
        """Handle search_knowledge_base tool call."""
        query = params.get('query', '')
        max_results = params.get('max_results', 5)
        category = params.get('category')

        if not query:
            return "Error: Search query is required."

        results = self.agent.kb.search(query, max_results=max_results)

        # Filter by category if specified
        if category:
            results = [r for r in results if r.get('category') == category]

        if not results:
            return (
                "No relevant documentation found for: " + query +
                "\n\nConsider escalating to human support or asking the customer for more details."
            )

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"**{r['title']}** (relevance: {r['score']:.2f}, category: {r['category']})\n"
                f"{r['content']}"
            )

        return "\n\n---\n\n".join(formatted)

    def _handle_create_ticket(self, params: dict) -> str:
        """Handle create_ticket tool call."""
        customer_id = params.get('customer_id', '')
        issue = params.get('issue', '')
        priority = params.get('priority', 'medium')
        channel = params.get('channel', 'web_form')
        category = params.get('category', 'general')

        if not customer_id or not issue:
            return "Error: customer_id and issue are required."

        # Get or create customer
        customer = self.memory.get_or_create_customer(
            email=customer_id if '@' in customer_id else None,
            phone=customer_id if '+' in customer_id else None,
            name=customer_id
        )

        # Create conversation
        conversation = self.memory.create_conversation(
            customer_id=customer.id,
            channel=channel,
            subject=issue[:100]
        )

        # Add initial message
        from memory_manager import Message
        msg = Message(
            conversation_id=conversation.id,
            channel=channel,
            direction='inbound',
            role='customer',
            content=issue
        )
        self.memory.add_message_to_conversation(conversation.id, msg)

        return (
            f"Ticket created successfully.\n"
            f"Ticket ID: {conversation.id}\n"
            f"Customer ID: {customer.id}\n"
            f"Channel: {channel}\n"
            f"Priority: {priority}\n"
            f"Status: open"
        )

    def _handle_get_history(self, params: dict) -> str:
        """Handle get_customer_history tool call."""
        customer_id = params.get('customer_id', '')

        if not customer_id:
            return "Error: customer_id is required."

        history = self.memory.get_customer_history(customer_id)

        if 'error' in history:
            return f"Error: {history['error']}"

        if history['total_conversations'] == 0:
            return "No previous interactions found for this customer."

        lines = [
            f"Customer: {history['customer'].get('name', 'Unknown')}",
            f"Email: {history['customer'].get('email', 'N/A')}",
            f"Total conversations: {history['total_conversations']}",
            f"Average sentiment: {history['customer'].get('avg_sentiment', 0.5):.2f}",
            ""
        ]

        for conv in history['conversations']:
            lines.append(
                f"Conversation {conv['id'][:8]}... | "
                f"Channel: {conv['initial_channel']} | "
                f"Status: {conv['status']} | "
                f"Sentiment: {conv['sentiment_score']:.2f} | "
                f"Messages: {conv['message_count']} | "
                f"Topics: {', '.join(conv['topics'])}"
            )

        return "\n".join(lines)

    def _handle_escalate(self, params: dict) -> str:
        """Handle escalate_to_human tool call."""
        ticket_id = params.get('ticket_id', '')
        reason = params.get('reason', 'cannot_answer')
        urgency = params.get('urgency', 'P2')

        if not ticket_id or not reason:
            return "Error: ticket_id and reason are required."

        self.memory.escalate_conversation(
            ticket_id,
            escalated_to="human_agent",
            reason=reason
        )

        escalation_id = f"ESC-{datetime.utcnow().strftime('%Y%m%d')}-{hash(ticket_id) % 10000:04d}"

        return (
            f"Escalation created successfully.\n"
            f"Escalation ID: {escalation_id}\n"
            f"Ticket ID: {ticket_id}\n"
            f"Reason: {reason}\n"
            f"Urgency: {urgency}\n"
            f"Status: awaiting_human_agent"
        )

    def _handle_send_response(self, params: dict) -> str:
        """Handle send_response tool call."""
        ticket_id = params.get('ticket_id', '')
        message = params.get('message', '')
        channel = params.get('channel', 'web_form')

        if not ticket_id or not message:
            return "Error: ticket_id and message are required."

        # Format for channel
        formatted = ResponseFormatter.format_for_channel(
            message, Channel(channel), ticket_id
        )

        # Add to conversation
        from memory_manager import Message
        msg = Message(
            conversation_id=ticket_id,
            channel=channel,
            direction='outbound',
            role='agent',
            content=message
        )
        self.memory.add_message_to_conversation(ticket_id, msg)

        return (
            f"Response sent successfully.\n"
            f"Ticket ID: {ticket_id}\n"
            f"Channel: {channel}\n"
            f"Delivery status: sent\n"
            f"Message length: {len(formatted)} characters"
        )

    def _handle_sentiment(self, params: dict) -> str:
        """Handle analyze_sentiment tool call."""
        message = params.get('message', '')

        if not message:
            return "Error: message is required."

        score = self.agent.sentiment_analyzer.analyze(message)

        if score >= 0.7:
            label = "positive"
        elif score >= 0.4:
            label = "neutral"
        elif score >= 0.3:
            label = "slightly negative"
        else:
            label = "negative"

        return (
            f"Sentiment Analysis Result:\n"
            f"Score: {score:.2f} (0.0 = very negative, 1.0 = very positive)\n"
            f"Label: {label}\n"
            f"Confidence: {'high' if score > 0.7 or score < 0.3 else 'medium' if score > 0.4 or score < 0.6 else 'low'}\n"
            f"Recommendation: {'Monitor closely' if score < 0.4 else 'Normal interaction'}"
        )

    def _handle_identify_customer(self, params: dict) -> str:
        """Handle identify_customer tool call."""
        email = params.get('email')
        phone = params.get('phone')
        name = params.get('name', '')

        if not email and not phone:
            return "Error: At least email or phone is required."

        customer = self.memory.get_or_create_customer(
            email=email, phone=phone, name=name
        )

        is_new = customer.total_interactions == 0

        return (
            f"Customer {'identified' if not is_new else 'created'}.\n"
            f"Customer ID: {customer.id}\n"
            f"Name: {customer.name or 'Unknown'}\n"
            f"Email: {customer.email or 'N/A'}\n"
            f"Phone: {customer.phone or 'N/A'}\n"
            f"Total interactions: {customer.total_interactions}\n"
            f"Average sentiment: {customer.avg_sentiment:.2f}\n"
            f"Preferred channel: {customer.preferred_channel}\n"
            f"{'New customer' if is_new else 'Returning customer'}"
        )

    # ─── Tool Execution ──────────────────────────────────────────────────

    def call_tool(self, tool_name: str, params: dict) -> str:
        """Execute a tool by name with given parameters."""
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'. Available tools: {', '.join(self.tools.keys())}"

        handler = self.tools[tool_name]['handler']
        try:
            return handler(params)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def get_tool_definitions(self) -> list:
        """Get MCP-compatible tool definitions."""
        return [
            {
                'name': tool['name'],
                'description': tool['description'],
                'inputSchema': tool['inputSchema']
            }
            for tool in self.tools.values()
        ]

    def get_server_info(self) -> dict:
        """Get server information."""
        return {
            'name': self.name,
            'version': self.version,
            'tools': list(self.tools.keys()),
            'tool_count': len(self.tools)
        }


# ─── CLI Runner ─────────────────────────────────────────────────────────────

def main():
    """Interactive CLI for testing the MCP server."""
    docs_path = os.path.join(os.path.dirname(__file__), '..', 'context', 'product-docs.md')
    server = MCPServer(docs_path=docs_path)

    print("=" * 60)
    print("  TechCorp Customer Success FTE — MCP Server")
    print("  Available tools:", ', '.join(server.tools.keys()))
    print("  Type 'quit' to exit, 'list' to see tools")
    print("=" * 60)

    while True:
        print("\n---")
        command = input("Tool name: ").strip()

        if command == 'quit':
            break

        if command == 'list':
            for name, tool in server.tools.items():
                print(f"\n{name}:")
                print(f"  {tool['description'][:100]}...")
                print(f"  Required: {tool['inputSchema'].get('required', [])}")
            continue

        if command not in server.tools:
            print(f"Unknown tool: {command}")
            continue

        # Get parameters
        tool = server.tools[command]
        required = tool['inputSchema'].get('required', [])
        properties = tool['inputSchema'].get('properties', {})

        params = {}
        print(f"Enter parameters for {command}:")
        for param_name, param_info in properties.items():
            is_required = param_name in required
            prompt = f"  {param_name}{'*' if is_required else ''} ({param_info['type']}): "
            value = input(prompt).strip()
            if value or is_required:
                # Type conversion
                if param_info['type'] == 'integer':
                    params[param_name] = int(value) if value else param_info.get('default', 0)
                else:
                    params[param_name] = value

        # Execute
        result = server.call_tool(command, params)
        print(f"\nResult:\n{result}")


if __name__ == "__main__":
    main()
