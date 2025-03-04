# SpeQL VSCode Extension

#### Installation

1. **Open VSCode**:
   - Launch your Visual Studio Code editor.

2. **Install SpeQLite Extension**:
   - Click on the `Extensions` tab in the sidebar.
   - Search for `SpeQL`.
   - Click the `Install` button next to the SpeQL extension.
   - After installation, the `SpeQL` icon will appear in the VSCode toolbar.

3. **Open SpeQL Panel**:
   - Click the `SpeQL` icon in the toolbar to open the SpeQL panel, then click `Click me` to configure SpeQL.

4. **Open Preview Panel**:
   - In the SpeQLite panel, click `Open Preview` to display the preview area.

5. **Create a New SQL File**:
   - Create a new `.sql` file in any folder within your project.

6. **Run Your First Query**:
   - Type the following query in the SQL editor:
     ```sql
     SELECT 1 AS one;
     ```
   - The running query and its result will appear in the preview panel.
   - As you edit your SQL queries, the results will update automatically. Differences between the editor and the preview are highlighted in the Diff window.
   - Now you have successfully installed and opened SpeQL. Great job!

7. **Details**:
   - Basically, you can trigger SpeQL in two ways:
   - **Automatic Trigger**:
      - SpeQL fetches the latest SQL editor input every 5 seconds.
   - **Manual Trigger**:
      - Press double `Enter` in the SQL editor to manually trigger SpeQL.
      - Upon triggering, a rotating icon will appear in the toolbar, changing to a checkmark once the result is ready.
   - **Note**:
     - SpeQL will prioritize the query at the cursor position. If your cursor is in a subquery, SpeQL will preview the subquery result.
     - It is recommended to keep only one SQL query in the editor. If there are multiple SQL queries in the editor, ensure they are separated by semicolons.

#### Advanced Features
*There are some advanced features to explore!*

1. **Debug Panel**:
   - **View Debug Information**:
     - SpeQL’s Debug panel displays debug information for your SQL query before execution. You don't need to wait too long to see the debug information.
   - **Accessing Debug Panel**:
     - Click the `SpeQL - Debug Info` button in the toolbar.
     - Alternatively, if you think the debug SQL is exactly what you want, you can press `Alt + M` to apply modifications to your SQL editor.

2. **Immediate Execution**:
   - Press `Ctrl + Enter` or click the `SpeQL - Execute` button in the toolbar to run SpeQL immediately.

3. **See Historical Traces**:
   - Click navigation buttons to see historical debug info and previews (at the upper right of each panel).