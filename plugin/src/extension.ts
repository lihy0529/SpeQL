// Copyright (c) 2025 Haoyu Li
// Released under the MIT License.
// See LICENSE file in the project root for details.

import * as vscode from "vscode";
import fetch from "node-fetch";
import { diffLines } from "diff";

let experimentalGroupIP = "47.76.206.205:5000";
let controlGroupIP = "47.76.206.205:5001";
let serverIP = controlGroupIP;
let panel: vscode.WebviewPanel | undefined;
let lastUserInput = "";
let lastModification = "";
let lastPreview = "";
let lastDebugModification = "";
let lastErrorInfo = "";
let lastSentContent: string = "";
let debugPanel: vscode.WebviewPanel | undefined;
let isEnabled = true;
let previewHistoryIndex = -1;
let previewHistory: Array<{ modCode: string; info: string }> = [];
let debugHistoryIndex = -1;
let debugHistory: Array<{ modCode: string; info: string }> = [];
let isControlGroup = true;

function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout | undefined;
  return (...args: any[]) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function activate(context: vscode.ExtensionContext) {
  const executeOnKeypress = vscode.commands.registerTextEditorCommand(
    "SpeQL.executeOnKeypress",
    () => {
      const editor = vscode.window.activeTextEditor;
      if (editor?.document.languageId === "sql") {
        vscode.commands.executeCommand("SpeQL.executeQuery");
      }
    }
  );

  const ipStatusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    100
  );
  ipStatusBarItem.text = "SpeQL $(sync~spin)";
  ipStatusBarItem.command = "SpeQL.setServerIP";

  vscode.window.onDidChangeActiveTextEditor((editor) => {
    if (editor && editor.document.languageId === "sql") {
      ipStatusBarItem.show();
    } else {
      ipStatusBarItem.hide();
    }
  });

  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor && activeEditor.document.languageId === "sql") {
    ipStatusBarItem.show();
  } else {
    ipStatusBarItem.hide();
  }

  context.subscriptions.push(ipStatusBarItem);

  const setIPCmd = vscode.commands.registerCommand(
    "SpeQL.setServerIP",
    async () => {
      let menuItems = isEnabled
        ? (isControlGroup
        ? [
            {
              label: "$(gear) Set Server IP",
              description: "Configure server connection",
            },
            {
              label: "$(play) Execute",
              description: "Execute current SQL query",
            },
            {
              label: `$(check) Disable SpeQL`,
              description: "Toggle SpeQL functionality",
            },
            {
              label: `$(check) Click me`,
              description: "Please click here to enable more features",
            },
          ]
        : [
            {
              label: "$(gear) Set Server IP",
              description: "Configure server connection",
            },
            {
              label: "$(preview) Open Preview",
              description: "Open SQL preview panel",
            },
            {
              label: "$(bug) Debug Info",
              description: "Let SpeQL help you debug",
            },
            {
              label: "$(play) Execute",
              description: "Execute current SQL query",
            },
            {
              label: `$(check) Disable SpeQL`,
              description: "Toggle SpeQL functionality",
            },
            {
              label: `$(x) Click me`,
              description: "No further actions are needed",
            },
          ])
          : [
            {
              label: `$(x) Enable SpeQL`,
              description: "Toggle SpeQL functionality",
            }
          ];

      const selection = await vscode.window.showQuickPick(menuItems, {
        placeHolder: "Select SpeQL action",
      });

      if (selection) {
        if (selection.label.includes("Set Server IP")) {
          const newIP = await vscode.window.showInputBox({
            prompt: "Enter SpeQL server connection (e.g., 127.0.0.1:5000)",
            value: serverIP ? serverIP : isControlGroup ? controlGroupIP : experimentalGroupIP,
          });
          if (newIP) {
            serverIP = newIP;
          }
        } else if (selection.label.includes("Open Preview")) {
          vscode.commands.executeCommand("SpeQL.openPreview");
        } else if (selection.label.includes("Debug")) {
          vscode.commands.executeCommand("SpeQL.openDebugInfo");
        } else if (selection.label.includes("Execute")) {
          vscode.commands.executeCommand("SpeQL.executeQuery");
        } else if (selection.label.includes("SpeQL")) {
          isEnabled = !isEnabled;
          ipStatusBarItem.text = `SpeQL ${
            isEnabled ? "$(sync~spin)" : "$(circle-slash)"
          }`;
        } else if (selection.label.includes("Click me")) {
          isControlGroup = !isControlGroup;
          if (isControlGroup) {
            serverIP = controlGroupIP;
          } else {
            serverIP = experimentalGroupIP;
          }
        }
      }
    }
  );

  const openPreviewCmd = vscode.commands.registerCommand(
    "SpeQL.openPreview",
    () => {
      if (panel && panel.visible) {
        panel.reveal(vscode.ViewColumn.Beside);
        return;
      }

      panel = vscode.window.createWebviewPanel(
        "SpeQLPreview",
        "Preview",
        vscode.ViewColumn.Beside,
        {
          enableScripts: true,
          retainContextWhenHidden: true,
        }
      );
      panel.webview.html = getWebviewContent("", "", "", "Preview", false, false);

      panel.webview.onDidReceiveMessage(
        (message) => {
          switch (message.command) {
            case "navigate_preview":
              if (message.direction != 0) {
                previewHistoryIndex += message.direction;
                if (previewHistoryIndex < 0) {
                  previewHistoryIndex = 0;
                }
                if (previewHistoryIndex >= previewHistory.length) {
                  previewHistoryIndex = previewHistory.length - 1;
                }
              } else {
                previewHistoryIndex = previewHistory.length - 1;
              }
              if (
                previewHistoryIndex >= 0 &&
                previewHistoryIndex < previewHistory.length &&
                panel
              ) {
                panel.webview.html = getWebviewContent(
                  previewHistory[previewHistoryIndex].modCode,
                  previewHistory[previewHistoryIndex].modCode,
                  previewHistory[previewHistoryIndex].info,
                  "Preview",
                  previewHistoryIndex > 0,
                  previewHistoryIndex < previewHistory.length - 1
                );
              }
              break;
          }
        },
        undefined,
        context.subscriptions
      );

      panel.onDidDispose(() => {
        panel = undefined;
      });
    }
  );

  const openDebugInfoCmd = vscode.commands.registerCommand(
    "SpeQL.openDebugInfo",
    () => {
      if (debugPanel && debugPanel.visible) {
        debugPanel.reveal(vscode.ViewColumn.Beside);
        return;
      }

      debugPanel = vscode.window.createWebviewPanel(
        "SpeQLDebugInfo",
        "Debug",
        vscode.ViewColumn.Beside,
        {
          enableScripts: true,
          retainContextWhenHidden: true,
        }
      );
      debugPanel.webview.html = getWebviewContent("", "", "", "Debug", false, false);

      debugPanel.webview.onDidReceiveMessage(
        (message) => {
          switch (message.command) {
            case "navigate_debug":
              if (message.direction != 0) {
                debugHistoryIndex += message.direction;
                if (debugHistoryIndex < 0) {
                  debugHistoryIndex = 0;
                }
                if (debugHistoryIndex >= debugHistory.length) {
                  debugHistoryIndex = debugHistory.length - 1;
                }
              } else {
                debugHistoryIndex = debugHistory.length - 1;
              }
              if (
                debugHistoryIndex >= 0 &&
                debugHistoryIndex < debugHistory.length &&
                debugPanel
              ) {
                debugPanel.webview.html = getWebviewContent(
                  debugHistory[debugHistoryIndex].modCode,
                  debugHistory[debugHistoryIndex].modCode,
                  debugHistory[debugHistoryIndex].info,
                  "Debug",
                  debugHistoryIndex > 0,
                  debugHistoryIndex < debugHistory.length - 1
                );
              }
              break;
          }
        },
        undefined,
        context.subscriptions
      );

      debugPanel.onDidDispose(() => {
        debugPanel = undefined;
      });
    }
  );

  const executeQueryCmd = vscode.commands.registerCommand(
    "SpeQL.executeQuery",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document.languageId !== "sql") {
        vscode.window.showErrorMessage("Please open a SQL file first");
        return;
      }

      const position = editor.selection.active;
      const prefix = editor.document.getText(
        new vscode.Range(new vscode.Position(0, 0), position)
      );
      const suffix = editor.document.getText(
        new vscode.Range(
          position,
          new vscode.Position(
            editor.document.lineCount - 1,
            editor.document.lineAt(editor.document.lineCount - 1).text.length
          )
        )
      );

      if (!panel) {
        panel = vscode.window.createWebviewPanel(
          "SpeQLPreview",
          "Preview",
          vscode.ViewColumn.Beside,
          {
            enableScripts: true,
            retainContextWhenHidden: true,
          }
        );
        panel.webview.html = getWebviewContent("", "", "", "Preview", false, false);

        panel.webview.onDidReceiveMessage(
          (message) => {
            switch (message.command) {
              case "navigate_preview":
                if (message.direction != 0) {
                  previewHistoryIndex += message.direction;
                } else {
                  previewHistoryIndex = previewHistory.length - 1;
                }
                if (
                  previewHistoryIndex >= 0 &&
                  previewHistoryIndex < previewHistory.length &&
                  panel
                ) {
                  panel.webview.html = getWebviewContent(
                    previewHistory[previewHistoryIndex].modCode,
                    previewHistory[previewHistoryIndex].modCode,
                    previewHistory[previewHistoryIndex].info,
                    "Preview",
                    previewHistoryIndex > 0,
                    previewHistoryIndex < previewHistory.length - 1
                  );
                }
                break;
            }
          },
          undefined,
          context.subscriptions
        );

        panel.onDidDispose(() => {
          panel = undefined;
        });
      }
      panel.reveal(vscode.ViewColumn.Beside);

      await sendServerRequest(prefix, suffix, controlGroupIP);
    }
  );

  const replaceWithDebugCmd = vscode.commands.registerCommand(
    "SpeQL.replaceWithDebug",
    () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor || editor.document.languageId !== "sql") {
        vscode.window.showErrorMessage("Please open a SQL file first");
        return;
      }

      if (debugHistoryIndex >= 0 && debugHistoryIndex < debugHistory.length) {
        const debugContent = debugHistory[debugHistoryIndex].modCode;
        const fullRange = new vscode.Range(
          new vscode.Position(0, 0),
          new vscode.Position(
            editor.document.lineCount - 1,
            editor.document.lineAt(editor.document.lineCount - 1).text.length
          )
        );
        editor.edit((editBuilder) => {
          editBuilder.replace(fullRange, debugContent);
        });
      }
    }
  );

  context.subscriptions.push(
    setIPCmd,
    openPreviewCmd,
    openDebugInfoCmd,
    executeQueryCmd,
    executeOnKeypress,
    replaceWithDebugCmd,
    ipStatusBarItem
  );

  const sendServerRequest = async (
    prefix: string,
    suffix: string,
    IP: string
  ) => {
    if (!prefix.trim() && !suffix.trim()) {
      return;
    }
    let currentContent = "";

    currentContent = `${prefix}/*CURSOR_IDENTIFIER*/${suffix}`;

    if (currentContent.trim() === lastSentContent.trim()) {
      return;
    }

    try {
      ipStatusBarItem.text = "SpeQL $(sync~spin)";
      lastSentContent = currentContent;
      const resp = await fetch(`http://${IP}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: currentContent }),
      });

      if (!resp.ok) {
        ipStatusBarItem.text = "SpeQL $(alert)";
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      for await (const chunk of resp.body) {
        const text = decoder.decode(Buffer.from(chunk as Buffer), {
          stream: true,
        });
        buffer += text;
        const lines = buffer.split("\n\n");

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              handleResponse(data, prefix, suffix);
            } catch (e) {
              console.error("Failed to parse SSE data:", line);
            }
          }
        }

        buffer = lines[lines.length - 1];
      }

      if (buffer.startsWith("data: ")) {
        try {
          const data = JSON.parse(buffer.slice(6));
          handleResponse(data, prefix, suffix);
        } catch (e) {
          console.error("Failed to parse SSE data:", buffer);
        }
      }
    } catch (error) {
      console.error("Error:", error);
      ipStatusBarItem.text = "SpeQL $(error)";
    }
  };

  const handleResponse = (data: any, prefix: string, suffix: string) => {
    if (!("complete" in data)) {
      lastUserInput = prefix + suffix;
      if ("modification" in data) {
        lastDebugModification = data.modification || "";
      } else {
        lastDebugModification = prefix + suffix;
      }
      if ("error_info" in data) {
        lastErrorInfo = data.error_info || "";
      } else {
        lastErrorInfo = "";
      }
      if (
        debugHistory.length == 0 ||
        lastDebugModification.trim() !=
          debugHistory[debugHistory.length - 1].modCode.trim()
      ) {
        debugHistory.push({
          modCode: lastDebugModification,
          info: lastErrorInfo,
        });
        if (debugHistoryIndex == debugHistory.length - 2) {
          debugHistoryIndex = debugHistory.length - 1;
        }

        setTimeout(() => {
          if (debugPanel) {
            debugPanel.webview.html = getWebviewContent(
              lastUserInput,
              debugHistory[debugHistoryIndex].modCode,
              debugHistory[debugHistoryIndex].info,
              "Debug",
              debugHistoryIndex > 0,
              debugHistoryIndex < debugHistory.length - 1
            );
          }
        }, 300);
      }
    }

    if (data.complete) {
      if (data.show && !data.modification) {
        ipStatusBarItem.text = "SpeQL $(alert)";
      } else {
        ipStatusBarItem.text = "SpeQL $(check)";
      }
    }

    if (data.show) {
      lastUserInput = prefix + suffix;
      lastModification = data.modification || "";
      lastPreview = data.preview || "";
      if (
        previewHistory.length == 0 ||
        lastModification.trim() !=
          previewHistory[previewHistory.length - 1].modCode.trim()
      ) {
        previewHistory.push({
          modCode: lastModification,
          info: lastPreview,
        });

        if (previewHistoryIndex == previewHistory.length - 2) {
          previewHistoryIndex = previewHistory.length - 1;
        }

        setTimeout(() => {
          if (panel) {
            panel.webview.html = getWebviewContent(
              lastUserInput,
              previewHistory[previewHistoryIndex].modCode,
              previewHistory[previewHistoryIndex].info,
              "Preview",
              previewHistoryIndex > 0,
              previewHistoryIndex < previewHistory.length - 1
            );
          }
        }, 300);
      }
    }
  };

  const debouncedSendRequest = debounce(sendServerRequest, 5000);

  vscode.workspace.onDidChangeTextDocument(async (e) => {
    if (!isEnabled) {
      return;
    }
    const editor = vscode.window.activeTextEditor;
    if (!editor || e.document !== editor.document) {
      return;
    }

    if (editor.document.languageId !== "sql") {
      return;
    }

    const position = editor.selection.active;

    let prefix = editor.document.getText(
      new vscode.Range(new vscode.Position(0, 0), position)
    );
    let suffix = editor.document.getText(
      new vscode.Range(
        position,
        new vscode.Position(
          editor.document.lineCount - 1,
          editor.document.lineAt(editor.document.lineCount - 1).text.length
        )
      )
    );
    if ((prefix + suffix).includes("/*CURSOR_IDENTIFIER*/")) {
      return;
    }
    if (suffix.trim().length === 0 && prefix.trim().endsWith(";")) {
      prefix = prefix.trim();
      prefix = prefix.substring(0, prefix.length - 1);
      suffix = "";
    }
    let content = ";" + prefix + "/*CURSOR_IDENTIFIER*/" + suffix + ";";
    const parts = content.split(";");
    const cursorPart = parts.find((part) =>
      part.includes("/*CURSOR_IDENTIFIER*/")
    );
    if (cursorPart) {
      content = cursorPart;
    }
    prefix = content.substring(0, content.indexOf("/*CURSOR_IDENTIFIER*/"));
    suffix = content.substring(
      content.indexOf("/*CURSOR_IDENTIFIER*/") + "/*CURSOR_IDENTIFIER*/".length
    );
    if (panel) {
      if (
        previewHistoryIndex >= 0 &&
        previewHistoryIndex < previewHistory.length
      ) {
        panel.webview.html = getWebviewContent(
          prefix + suffix,
          previewHistory[previewHistoryIndex].modCode,
          previewHistory[previewHistoryIndex].info,
          "Preview",
          previewHistoryIndex > 0,
          previewHistoryIndex < previewHistory.length - 1
        );
      }
    }
    if (debugPanel) {
      if (debugHistoryIndex >= 0 && debugHistoryIndex < debugHistory.length) {
        debugPanel.webview.html = getWebviewContent(
          prefix + suffix,
          debugHistory[debugHistoryIndex].modCode,
          debugHistory[debugHistoryIndex].info,
          "Debug",
          debugHistoryIndex > 0,
          debugHistoryIndex < debugHistory.length - 1
        );
      }
    }

    const changes = e.contentChanges;
    const isEnterKey = changes.length > 0 && changes[0].text.includes("\n");
    if (!isControlGroup) {
      if (isEnterKey) {
        await sendServerRequest(prefix, suffix, serverIP);
      }
      debouncedSendRequest(prefix, suffix, serverIP);
    }
  });
}

export function deactivate() {}

function getWebviewContent(
  userCode: string,
  modCode: string,
  info: string,
  type: string,
  canGoBack: boolean = false,
  canGoForward: boolean = false
) {
  const commandName = type.toLowerCase();

  userCode = userCode
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0)
    .join("\n");

  modCode = modCode
    .split("\n")
    .map((line) => line.trimEnd())
    .filter((line) => line.length > 0)
    .join("\n");

  const diffParts = diffLines(modCode, userCode);
  let differences = "";

  diffParts.forEach((part) => {
    const escapedText = escapeHtml(part.value);
    if (part.added) {
      differences += `<div class="diff-added"><pre><code class="language-sql">${escapedText}</code></pre></div>`;
    } else if (part.removed) {
      differences += `<div class="diff-removed"><pre><code class="language-sql">${escapedText}</code></pre></div>`;
    } else {
      differences += `<div class="diff-unchanged"><pre><code class="language-sql">${escapedText}</code></pre></div>`;
    }
  });

  return `
  <html>
  <head>
    <meta charset="UTF-8"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sql.min.js"></script>
    <style>
      body {
        margin: 0;
        padding: 0;
        background: var(--vscode-editor-background);
        color: var(--vscode-editor-foreground);
        font-family: var(--vscode-editor-font-family);
        font-size: var(--vscode-editor-font-size);
        -webkit-font-smoothing: antialiased;
      }
      .split-container {
        display: flex;
        flex-direction: column;
        height: 100vh;
        position: relative;
      }
      .split {
        overflow: auto;
        padding: 0 16px !important;
      }
      .diff {
        height: calc(50% - 4px);
        background: var(--vscode-editor-background);
        color: var(--vscode-editor-foreground);
      }
      .${type} {
        height: calc(50% - 4px);
        background: var(--vscode-editor-background);
        color: var(--vscode-editor-foreground);
      }
      .resizer {
        height: 8px;
        background: var(--vscode-editorWidget-border);
        cursor: row-resize;
      }
      h2 {
        margin: 8px 0 8px !important;
        font-weight: bold;
        font-size: 1.1em;
      }
      .diff-added, .diff-added pre, .diff-added code {
        background-color: rgba(35, 134, 54, 0.3) !important;
        color: #e6e6e6 !important;
        text-shadow: none !important;
        line-height: 1.4 !important;
        opacity: 1 !important;
      }
      .diff-removed, .diff-removed pre, .diff-removed code {
        background-color: rgba(219, 88, 96, 0.3) !important;
        color: #e6e6e6 !important;
        text-shadow: none !important;
        line-height: 1.4 !important;
        opacity: 1 !important;
      }
      .diff-unchanged, .diff-unchanged pre, .diff-unchanged code {
        background-color: transparent !important;
        color: #e6e6e6 !important;
        text-shadow: none !important;
        line-height: 1.4 !important;
        opacity: 1 !important;
      }
      pre, code {
        color: #e6e6e6 !important;
        font-weight: 500 !important;
      }
      pre {
        white-space: pre-wrap;
        word-wrap: break-word;
        margin: 0 !important;
        padding: 0 !important;
        background: transparent !important;
      }
      code {
        background: transparent !important;
      }
      .language-sql {
        background: transparent !important;
      }
      pre[class*="language-"],
      code[class*="language-"] {
        background: inherit !important;
        color: inherit !important;
      }

      .language-sql,
      .language-sql span,
      [class*="language-"],
      pre[class*="language-"],
      code[class*="language-"],
      .token {
        text-shadow: none !important;
        background: none !important;
        color: inherit !important;
        font-family: inherit !important;
        font-weight: inherit !important;
        text-align: inherit !important;
        white-space: inherit !important;
        word-spacing: normal !important;
        word-break: normal !important;
        word-wrap: normal !important;
        line-height: inherit !important;
        -moz-tab-size: 4 !important;
        -o-tab-size: 4 !important;
        tab-size: 4 !important;
      }

      pre, code {
        color: #c9d1d9 !important;
        font-weight: 400 !important;
        background: transparent !important;
        margin: 0 !important;
        padding: 0 !important;
      }

      .${type} pre,
      .${type} code {
        white-space: pre !important;
        overflow-x: auto !important;
      }

      .diff pre,
      .${type} pre {
        padding-left: 8px !important;
      }

      .diff pre,
      .diff code {
        white-space: pre-wrap !important;
        word-wrap: break-word !important;
      }

      .token.keyword { color: #ff7b72 !important; }
      .token.string { color: #a5d6ff !important; }
      .token.number { color: #79c0ff !important; }
      .token.function { color: #d2a8ff !important; }
      .token.operator { color: #79c0ff !important; }
      .token.comment { color: #8b949e !important; }

      .token {
        background: none !important;
        text-shadow: none !important;
        font-weight: inherit !important;
        font-style: inherit !important;
      }

      pre, code {
        color: #c9d1d9 !important;
        font-weight: 400 !important;
        background: transparent !important;
      }

      .navigation {
        position: absolute;
        top: 8px;
        right: 16px;
        display: flex;
        gap: 4px;
        z-index: 1000;
      }
      .nav-button {
        padding: 2px 6px;
        background: transparent;
        color: var(--vscode-editor-foreground);
        border: 1px solid var(--vscode-editor-foreground);
        border-radius: 3px;
        cursor: pointer;
        font-size: 14px;
        opacity: 0.6;
      }
      .nav-button:disabled {
        opacity: 0.2;
        cursor: not-allowed;
      }
      .nav-button:not(:disabled):hover {
        opacity: 1;
      }

      .debug-tooltip {
        position: absolute;
        bottom: 8px;
        right: 16px;
        color: var(--vscode-editor-foreground);
        opacity: 0.6;
        font-size: 12px;
      }
    </style>
  </head>
  <body>
    <div class="split-container">
      <div class="navigation">
        <button class="nav-button" onclick="navigate_${commandName}(-1)" ${
    !canGoBack ? "disabled" : ""
  }>
          ‹
        </button>
        <button class="nav-button" onclick="navigate_${commandName}(1)" ${
    !canGoForward ? "disabled" : ""
  }>
          ›
        </button>
        <button class="nav-button" onclick="navigate_${commandName}(0)" ${
    !canGoForward ? "disabled" : ""
  }>
          ↺
        </button>
      </div>
      <div class="split diff">
        <h2>Diff</h2>
        ${differences}
      </div>
      ${
        info
          ? `
        <div class="resizer" onmousedown="startResizing(event)"></div>
        <div class="split ${type}">
          <h2>${type}</h2>
          ${
            commandName === "preview"
              ? `
            <pre><code class="language-sql">${escapeHtml(info)}</code></pre>
          `
              : `
            <pre><code class="language-text">${escapeHtml(info)}</code></pre>
          `
          }
        </div>
      `
          : ""
      }
      ${type === 'Debug' ? '<div class="debug-tooltip">Alt+M to apply</div>' : ''}
    </div>
    <script>
      let isResizing = false;
      let lastY = 0;
      const diffDiv = document.querySelector('.diff');
      const ${type}Div = document.querySelector('.${type}');
      const resizer = document.querySelector('.resizer');

      function startResizing(event) {
        isResizing = true;
        lastY = event.clientY;
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResizing);
      }

      function resize(event) {
        if (!isResizing) return;

        const diffHeight = diffDiv.offsetHeight;
        const deltaY = event.clientY - lastY;
        const newHeight = diffHeight + deltaY;
        
        diffDiv.style.height = newHeight + 'px';
        ${type}Div.style.height = 'calc(100% - ' + (newHeight + resizer.offsetHeight) + 'px)';
        
        lastY = event.clientY;
      }

      function stopResizing() {
        isResizing = false;
        document.removeEventListener('mousemove', resize);
        document.removeEventListener('mouseup', stopResizing);
      }

      resizer.addEventListener('mousedown', startResizing);
      Prism.highlightAll();

      function navigate_${commandName}(direction) {
        const vscode = acquireVsCodeApi();
        vscode.postMessage({
          command: 'navigate_${commandName}',
          direction: direction
        });
      }
    </script>
  </body>
  </html>
  `;
}

function escapeHtml(str: string) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
