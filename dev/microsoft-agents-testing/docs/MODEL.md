# Microsoft Agents Testing model

This model describes the main runtime contracts in `microsoft_agents.testing`,
their concrete implementations, and the data that moves between them. Solid
arrows represent inheritance, dotted arrows represent protocol implementation
or use, diamonds represent ownership, and plain arrows represent creation or
data flow.

## Abstractions at a glance

```mermaid
classDiagram
    direction LR

    class Scenario {
        <<abstract>>
    }
    class ScenarioConfig
    class ClientConfig
    class ClientFactory {
        <<Protocol>>
    }
    class AgentClient
    class Sender {
        <<abstract>>
    }
    class CallbackServer {
        <<abstract>>
    }
    class Transcript
    class Exchange
    class ExpectBase {
        <<generic>>
    }
    class SelectBase {
        <<generic>>
    }
    class TranscriptFormatter {
        <<Protocol>>
    }

    Scenario *-- ScenarioConfig
    ScenarioConfig *-- ClientConfig
    Scenario ..> ClientFactory : yields
    ClientFactory ..> AgentClient : creates

    AgentClient o-- Sender : sends through
    AgentClient o-- Transcript : observes
    Sender ..> Exchange : produces
    Sender ..> Transcript : records into
    CallbackServer ..> Transcript : records callbacks into
    Transcript *-- "0..*" Exchange

    AgentClient ..> ExpectBase : asserts with
    AgentClient ..> SelectBase : queries with
    TranscriptFormatter ..> Transcript : formats
```

## External agent interaction

```mermaid
flowchart LR
    subgraph TestProcess["Test process"]
        Test["Test code"]
        Scenario["ExternalScenario"]
        Factory["ClientFactory"]
        Client["AgentClient"]
        Sender["Sender"]
        Callback["CallbackServer"]
        Transcript["Transcript"]
        Fluent["ExpectBase / SelectBase"]

        Test --> Scenario
        Scenario --> Factory
        Factory --> Client
        Client --> Sender
        Client --> Fluent
        Client --> Transcript
        Sender -->|"records request Exchange"| Transcript
        Callback -->|"records callback Exchange"| Transcript
        Fluent -->|"queries and asserts over"| Transcript
    end

    Agent["Externally hosted agent"]

    Sender -->|"POST Activity"| Agent
    Agent -->|"HTTP acknowledgement, expect_replies, or invoke result"| Sender
    Agent -->|"POST outgoing Activity to service_url"| Callback
```

## Structural model

```mermaid
classDiagram
    direction LR

    namespace Configuration {
        class ClientConfig {
            +dict~str, str~ headers
            +str auth_token
            +ActivityTemplate activity_template
            +with_headers(**headers) ClientConfig
            +with_auth_token(token) ClientConfig
            +with_template(template) ClientConfig
        }

        class ScenarioConfig {
            +str env_file_path
            +int callback_server_port
            +ClientConfig client_config
        }
    }

    namespace Scenarios {
        class ClientFactory {
            <<Protocol>>
            +__call__(config) AgentClient
        }

        class Scenario {
            <<abstract>>
            +run() AsyncContextManager~ClientFactory~
            +client(config) AsyncIterator~AgentClient~
        }

        class ExternalScenario
    }

    namespace Client {
        class AgentClient {
            +ActivityTemplate template
            +Transcript transcript
            +recent() list~Activity~
            +history() list~Activity~
            +ex_recent() list~Exchange~
            +ex_history() list~Exchange~
            +clear()
            +ex_send(activity_or_text, wait) list~Exchange~
            +send(activity_or_text, wait) list~Activity~
            +ex_send_expect_replies(activity_or_text) list~Exchange~
            +send_expect_replies(activity_or_text) list~Activity~
            +ex_invoke(activity) Exchange
            +invoke(activity) InvokeResponse
            +select(history) ActivitySelect
            +expect(history) ActivityExpect
            +ex_select(history) ExchangeSelect
            +ex_expect(history) ExchangeExpect
            +child() AgentClient
        }

        class ActivityTemplate
    }

    namespace Transport {
        class Sender {
            <<abstract>>
            +send(activity, transcript, **kwargs) Exchange
        }

        class AiohttpSender

        class CallbackServer {
            <<abstract>>
            +listen(transcript) AsyncIterator~Transcript~
        }

        class AiohttpCallbackServer {
            +str service_endpoint
        }
    }

    namespace TranscriptModel {
        class Transcript {
            -Transcript parent
            -list~Transcript~ children
            -list~Exchange~ history
            +record(exchange)
            +history() list~Exchange~
            +child() Transcript
            +get_root() Transcript
            +clear()
        }

        class Exchange {
            +Activity request
            +datetime request_at
            +int status_code
            +str body
            +InvokeResponse invoke_response
            +str error
            +list~Activity~ responses
            +datetime response_at
            +bool is_error
            +timedelta latency
            +float latency_ms
        }

        class Activity {
            <<external SDK model>>
        }

        class InvokeResponse {
            <<external SDK model>>
        }
    }

    namespace FluentAPI {
        class ExpectBase~ModelT~ {
            +that(criteria) Self
            +that_for_any(criteria) Self
            +that_for_all(criteria) Self
            +that_for_none(criteria) Self
            +that_for_one(criteria) Self
            +that_for_exactly(n, criteria) Self
            +has_count(n) Self
        }

        class SelectBase~ModelT~ {
            +where(criteria) Self
            +where_not(criteria) Self
            +order_by(key) Self
            +first(n) Self
            +last(n) Self
            +at(n) Self
            +sample(n) Self
            +expect() Expect
            +get() list~ModelT~
        }

        class ActivityExpect["ActivityExpect<br/>ExpectBase&lt;Activity&gt;"]
        class ExchangeExpect["ExchangeExpect<br/>ExpectBase&lt;Exchange&gt;"]
        class ActivitySelect["ActivitySelect<br/>SelectBase&lt;Activity&gt;"]
        class ExchangeSelect["ExchangeSelect<br/>SelectBase&lt;Exchange&gt;"]
    }

    namespace Formatting {
        class TranscriptFormatter {
            <<Protocol>>
            +format(transcript) str
        }

        class BaseTranscriptFormatter {
            +__call__(transcript) str
            +format(transcript) str
        }

        class ActivityTranscriptFormatter
        class ConversationTranscriptFormatter
        class JsonTranscriptFormatter
    }

    ScenarioConfig *-- ClientConfig
    Scenario *-- ScenarioConfig
    Scenario ..> ClientFactory : run yields
    ClientFactory ..> AgentClient : creates

    Scenario <|-- ExternalScenario

    ExternalScenario ..> AiohttpCallbackServer : starts
    ExternalScenario ..> ClientFactory : configures

    AgentClient o-- Sender
    AgentClient o-- Transcript
    AgentClient o-- ActivityTemplate
    Sender <|-- AiohttpSender
    CallbackServer <|-- AiohttpCallbackServer
    Sender ..> Exchange : returns
    Sender ..> Transcript : records into
    AiohttpCallbackServer ..> Transcript : creates or accepts

    Transcript *-- "0..*" Exchange
    Transcript o-- "0..*" Transcript : child scopes
    Exchange o-- "0..*" Activity : request and responses
    Exchange o-- "0..1" InvokeResponse

    ExpectBase <|-- ActivityExpect
    ExpectBase <|-- ExchangeExpect
    SelectBase <|-- ActivitySelect
    SelectBase <|-- ExchangeSelect
    ActivitySelect ..> ActivityExpect : creates
    ExchangeSelect ..> ExchangeExpect : creates
    AgentClient ..> ActivitySelect : creates
    AgentClient ..> ActivityExpect : creates
    AgentClient ..> ExchangeSelect : creates
    AgentClient ..> ExchangeExpect : creates

    TranscriptFormatter <|.. ActivityTranscriptFormatter
    TranscriptFormatter <|.. ConversationTranscriptFormatter
    TranscriptFormatter <|.. JsonTranscriptFormatter
    BaseTranscriptFormatter <|-- ActivityTranscriptFormatter
    BaseTranscriptFormatter <|-- ConversationTranscriptFormatter
    BaseTranscriptFormatter <|-- JsonTranscriptFormatter
    TranscriptFormatter ..> Transcript : formats
```

## Runtime interaction

The scenario owns the test-infrastructure lifetime. It starts the callback
server and yields a factory whose clients share the callback transcript.
Standard replies arrive as separate callback exchanges, while
`expect_replies` activities and invokes are represented by the HTTP exchange.

```mermaid
sequenceDiagram
    actor Test
    participant Scenario
    participant Factory as ClientFactory
    participant Client as AgentClient
    participant Sender
    participant Agent as Agent endpoint
    participant Callback as CallbackServer
    participant Transcript

    Test->>Scenario: run()
    activate Scenario
    Scenario->>Callback: listen()
    activate Callback
    Callback-->>Scenario: shared Transcript
    Scenario->>Factory: bind agent URL, callback URL, defaults, Transcript
    Scenario-->>Test: yield ClientFactory

    Test->>Factory: create(config)
    Factory->>Sender: create for agent endpoint
    Factory->>Client: create(Sender, Transcript, ActivityTemplate)
    Factory-->>Test: AgentClient

    Test->>Client: send() or ex_send()
    Client->>Client: build Activity from template
    Client->>Sender: send(Activity, Transcript)
    activate Sender
    Sender->>Agent: POST activity

    alt standard asynchronous reply
        Agent->>Callback: POST activity
        Callback->>Transcript: record response-only Exchange
        Callback-->>Agent: HTTP 200
        Agent-->>Sender: HTTP acknowledgement
        Sender->>Transcript: record request Exchange
    else expect_replies delivery mode
        Agent-->>Sender: HTTP response containing activities
        Sender->>Sender: parse activities into Exchange.responses
        Sender->>Transcript: record request-response Exchange
    else invoke activity
        Agent-->>Sender: HTTP invoke response
        Sender->>Sender: parse Exchange.invoke_response
        Sender->>Transcript: record invoke Exchange
    end

    Sender-->>Client: Exchange
    deactivate Sender

    opt wait is greater than zero
        Client->>Client: wait, then read accumulated Transcript
    end

    Client-->>Test: Exchange list or mapped response Activities
    Test->>Client: expect() / select() over Transcript snapshot
    Test->>Scenario: exit context
    Scenario->>Factory: cleanup()
    Scenario->>Callback: stop
    deactivate Callback
    deactivate Scenario
```

## Scope notes

The model includes supporting contracts and public types needed to make the
remaining relationships complete:

- `ClientFactory`, the contract yielded by every `Scenario`.
- `AiohttpSender` and `AiohttpCallbackServer`, the concrete transport pair.
- `ActivityTemplate` and the typed `Activity*` / `Exchange*` fluent wrappers
  exposed by `AgentClient`.
- The three built-in transcript formatter implementations.

`ScenarioRegistry` and CLI/pytest integration are intentionally outside this
runtime model. They discover and inject scenarios but do not alter the core
scenario-client-transport-transcript contracts. They would be the next useful
diagram if package registration and test-runner integration need documenting.
