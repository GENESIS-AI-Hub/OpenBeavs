<script>
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { WEBUI_API_BASE_URL } from '$lib/constants';

	let messages = [];
	let prompt = '';
	let loading = false;
	let chatId = null;
	let agentId = null;
	let agentName = 'Agent';
	let error = null;
    let agentUrl = '';

	const registerAgent = async (url) => {
		try {
			const res = await fetch(`${WEBUI_API_BASE_URL}/agents/register-by-url`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					agent_url: url
				})
			});

			if (!res.ok) {
				const data = await res.json();
				throw new Error(data.detail || 'Failed to register agent');
			}

			return await res.json(); // Returns agent object
		} catch (e) {
			console.error(e);
			error = `Error registering agent: ${e.message}`;
			return null;
		}
	};

	const createChat = async (agentId) => {
		try {
			const res = await fetch(`${WEBUI_API_BASE_URL}/chats`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					title: 'New Chat',
					agent_id: agentId
				})
			});

			if (!res.ok) {
				throw new Error('Failed to create chat');
			}

			return await res.json();
		} catch (e) {
			console.error(e);
			error = `Error creating chat: ${e.message}`;
			return null;
		}
	};

	const sendMessage = async () => {
		if (!prompt.trim() || !chatId) return;

		const content = prompt;
		prompt = '';
		loading = true;

		// Optimistic update
		messages = [
			...messages,
			{
				role: 'user',
				content: content,
				timestamp: new Date().toISOString()
			}
		];
        
        await tick();
        scrollToBottom();

		try {
			const res = await fetch(`${WEBUI_API_BASE_URL}/chats/${chatId}/messages`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					content: content
				})
			});

			if (!res.ok) {
				throw new Error('Failed to send message');
			}

			const data = await res.json(); // Returns assistant message
			messages = [...messages, data];
            await tick();
            scrollToBottom();

		} catch (e) {
			console.error(e);
			messages = [
				...messages,
				{
					role: 'system',
					content: `Error: ${e.message}`,
					timestamp: new Date().toISOString()
				}
			];
		} finally {
			loading = false;
		}
	};
    
    const scrollToBottom = () => {
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

	const handleExpand = () => {
		if (chatId) {
			window.open(`${window.location.origin}/c/${chatId}`, '_blank');
		}
	};

    const handleKeydown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    }

	// Hardcoded agent URL for now
	const DEFAULT_AGENT_URL = 'https://hello-world-gxfr.onrender.com';

	onMount(async () => {
		// Use query param if present, otherwise fallback to hardcoded URL
		agentUrl = $page.url.searchParams.get('agent_url') || DEFAULT_AGENT_URL;

		if (!agentUrl) {
			error = 'No agent URL provided.';
			return;
		}

		loading = true;
		const agent = await registerAgent(agentUrl);

		if (agent) {
			agentId = agent.id;
			agentName = agent.name;
			const chat = await createChat(agentId);

			if (chat) {
				chatId = chat.id;
			}
		}
		loading = false;
	});
</script>

<div class="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-sans">
	<!-- Header -->
	<div class="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
		<div class="flex items-center gap-2">
			<div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
			<div class="font-medium text-sm truncate max-w-[150px]">{agentName}</div>
		</div>
        <div class="flex gap-2">
    		<button
    			on:click={handleExpand}
    			class="p-1.5 text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
                title="Open in full screen"
    		>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" />
                </svg>
    		</button>
        </div>
	</div>

	<!-- Chat Area -->
	<div id="chat-container" class="flex-1 overflow-y-auto p-4 space-y-4">
		{#if error}
			<div class="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm">
				{error}
			</div>
		{/if}

		{#if messages.length === 0 && !loading && !error}
            <div class="flex flex-col items-center justify-center h-full text-center text-gray-500 dark:text-gray-400 p-8 opacity-60">
                <div class="w-12 h-12 mb-3 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 dark:text-blue-400">
                     <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.159 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" />
                    </svg>
                </div>
                <p class="text-sm">Start a conversation with {agentName}.</p>
            </div>
		{/if}

		{#each messages as message}
			<div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
				<div
					class="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm shadow-sm
                    {message.role === 'user'
						? 'bg-blue-600 text-white rounded-br-none'
						: 'bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none'}"
				>
					{message.content}
				</div>
			</div>
		{/each}

		{#if loading}
			<div class="flex justify-start">
				<div class="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-none px-4 py-3 flex items-center gap-1">
					<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
					<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
					<div class="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Input Area -->
	<div class="p-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
		<div class="relative flex items-center">
			<input
				bind:value={prompt}
                on:keydown={handleKeydown}
				placeholder="Type a message..."
                disabled={loading || !!error}
				class="w-full pl-4 pr-10 py-3 bg-gray-100 dark:bg-gray-900 border-0 rounded-full focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-600 focus:outline-none text-sm transition-all"
			/>
			<button
				on:click={sendMessage}
				disabled={!prompt.trim() || loading || !!error}
				class="absolute right-2 p-1.5 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="currentColor"
					class="w-4 h-4 transform rotate-90"
				>
					<path
						d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z"
					/>
				</svg>
			</button>
		</div>
        <div class="text-[10px] text-center mt-2 text-gray-400 dark:text-gray-500">
            Powered by Gemini
        </div>
	</div>
</div>
