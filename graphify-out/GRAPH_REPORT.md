# Graph Report - .  (2026-07-23)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1413 nodes · 3051 edges · 95 communities (70 shown, 25 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 109 edges (avg confidence: 0.58)
- Token cost: 3,534 input · 1,081 output

## Graph Freshness
- Built from commit: `46c81602`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Pinia Store Lifecycle
- Django API Serializers
- Vue VNode Creation
- Vue Component Hooks
- Vue Instance Setup
- Excel Grid Logic
- Vue Renderer Core
- Excel Grid Actions
- Vue Custom Elements
- Vue Devtools Internals
- Vue Props and Attributes
- Vue Router Error Handling
- Vue Reactivity Engine
- Django Database Models
- Assays Management View
- Corrective Tasks View
- Sampling Management View
- Status Tasks View
- General Tasks View
- Weekly Dashboard View
- Vue Scheduler and Formatting
- Pinia and Reactivity Composition
- Devtools Component Inspection
- Group Schedule View
- Equipments Management View
- Areas Management View
- Users Management View
- Pinia Devtools Integration
- Monthly Calendar View
- Samples Management View
- Plants Management View
- Systems Management View
- User Permissions View
- Vue Hook Management
- Vue Reactivity Core
- Devtools Plugin Registry
- Vue Router Utilities
- Vue Reactivity Utilities
- Pinia HMR and Devtools
- Vue Router Guard Logic
- Vue DOM Utilities
- Weekly Tasks Component
- Data Serialization Utilities
- Project Dependencies
- Equipment Hierarchy API
- Devtools Setup Utilities
- Grid Interaction Handlers
- Vue Router Composition API
- Frontend Package Configuration
- Grid Formatting Utilities
- Router Instance Logic
- App Layout Components
- Vue Router History
- Object Utility Functions
- URL Query Encoding
- Router Path Matching
- Vite Build Dependencies
- Grid Data Helpers
- URL Parsing Utilities
- Corrective Task Migrations
- State Field Migrations
- Task Catalog Migrations
- Task Database Entities
- Excel Export Utility
- Django App Configuration
- Django Admin CLI
- API Pagination Logic
- Base Table Component
- Grid Cell Navigation
- Grid Resize Logic
- ASGI Server Config
- Django Project Settings
- WSGI Server Config
- Initial Database Migration
- Task Reschedule Migration
- Assay ID Migration
- Assay Timestamp Migration
- Assay Constraints Migration
- Task Relationship Migration
- Task Cleanup Migration
- Task Shift Migration
- Task Foreign Key Migration
- Task Catalog Schema
- Task Name Refactor
- Weather API Composable
- Dependency Configuration
- Weather State Store

## God Nodes (most connected - your core abstractions)
1. `warn$1()` - 61 edges
2. `baseCreateRenderer()` - 50 edges
3. `push()` - 40 edges
4. `setup()` - 38 edges
5. `forEach()` - 29 edges
6. `get()` - 28 edges
7. `toRaw()` - 28 edges
8. `createSetupStore()` - 25 edges
9. `User` - 21 edges
10. `value()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `createRouter()` --indirect_call--> `push()`  [INFERRED]
  frontend/vue_app/.vite/deps/vue-router.js → frontend/vue_app/.vite/deps/chunk-IJV5NOMV.js
- `useHistoryStateNavigation()` --indirect_call--> `push()`  [INFERRED]
  frontend/vue_app/.vite/deps/vue-router.js → frontend/vue_app/.vite/deps/chunk-IJV5NOMV.js
- `loadData()` --indirect_call--> `values()`  [INFERRED]
  frontend/vue_app/src/views/genericViews/AssaysView.vue → frontend/vue_app/.vite/deps/chunk-IJV5NOMV.js
- `loadData()` --indirect_call--> `values()`  [INFERRED]
  frontend/vue_app/src/views/genericViews/STasksViews.vue → frontend/vue_app/.vite/deps/chunk-IJV5NOMV.js
- `loadData()` --indirect_call--> `values()`  [INFERRED]
  frontend/vue_app/src/views/genericViews/UserPsView.vue → frontend/vue_app/.vite/deps/chunk-IJV5NOMV.js

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Weather Feature Flow** — frontend_vue_app_src_stores_weatherstore, frontend_vue_app_src_composable_useweather, frontend_vue_app_src_helpers_getweather [EXTRACTED 0.90]
- **Database Normalization Proposal** — db_normalization_analysis_task, db_normalization_analysis_correctivetask, db_normalization_analysis_taskcatalog [EXTRACTED 1.00]

## Communities (95 total, 25 thin omitted)

### Community 0 - "Pinia Store Lifecycle"
Cohesion: 0.04
Nodes (39): getCurrentScope(), hasInjectionContext(), onScopeDispose(), addSubscription(), basename(), bom(), classify(), click() (+31 more)

### Community 1 - "Django API Serializers"
Cohesion: 0.05
Nodes (37): APIView, URL configuration for data4cdp_v1 project.  The `urlpatterns` list routes URLs t, AreaSerializer, AssaySerializer, CalendarSerializer, CorrectiveTaskSerializer, EquipmentSerializer, EstadoSerializer (+29 more)

### Community 2 - "Vue VNode Creation"
Cohesion: 0.05
Nodes (50): createBaseVNode(), createBlock(), createCommentVNode(), createElementBlock(), createSlots(), createStaticVNode(), createTextVNode(), customRef() (+42 more)

### Community 3 - "Vue Component Hooks"
Cohesion: 0.08
Nodes (40): apply(), beforeMount(), beforeUnmount(), beforeUpdate(), callModelHook(), created(), entries(), filter() (+32 more)

### Community 4 - "Vue Instance Setup"
Cohesion: 0.12
Nodes (39): applyOptions(), callHook(), callWithAsyncErrorHandling(), callWithErrorHandling(), createComponentInstance(), createDevRenderContext(), createDuplicateChecker(), createPathGetter() (+31 more)

### Community 5 - "Excel Grid Logic"
Cohesion: 0.05
Nodes (24): activeCell, activeFilters, clipboardInput, colWidths, containerRef, currentUniqueValues, filteredGrid, filteredUniqueValues (+16 more)

### Community 6 - "Vue Renderer Core"
Cohesion: 0.09
Nodes (27): baseCreateRenderer(), createAppAPI(), createAppContext(), createHydrationRenderer(), createRenderer(), endMeasure(), ensureHydrationRenderer(), ensureRenderer() (+19 more)

### Community 7 - "Excel Grid Actions"
Cohesion: 0.07
Nodes (23): activeCell, addCol(), clipboardInput, colWidths, fallbackCopy(), focusCell(), getLetter(), grid (+15 more)

### Community 8 - "Vue Custom Elements"
Cohesion: 0.19
Nodes (15): _applyStyles(), connectedCallback(), constructor(), _createVNode(), guardReactiveProps(), _injectChildStyle(), isProxy(), _mount() (+7 more)

### Community 9 - "Vue Devtools Internals"
Cohesion: 0.05
Nodes (47): addSub(), assertNumber(), assertType(), autoPrefix(), createDevtoolsComponentHook(), createDevtoolsPerformanceHook(), createSuspenseBoundary(), devtoolsComponentEmit() (+39 more)

### Community 10 - "Vue Props and Attributes"
Cohesion: 0.11
Nodes (24): createHydrationFunctions(), createPropsRestProxy(), getEscapedCssVarName(), includeBooleanAttr(), includes(), invokeVNodeHook(), isMismatchAllowed(), isRenderableAttrValue() (+16 more)

### Community 11 - "Vue Router Error Handling"
Cohesion: 0.07
Nodes (8): [
    2
    /* ErrorTypes.NAVIGATION_GUARD_REDIRECT */
  ](), createRouteRecordMatcher(), normalizeRecordProps(), normalizeRouteRecord(), TODO: could we use a symbol in the future?, TODO: should be kept in queue, stringifyRoute(), tokenizePath()

### Community 12 - "Vue Reactivity Engine"
Cohesion: 0.08
Nodes (32): batch(), cleanupDeps(), cleanupEffect(), closeBlock(), deleteProperty(), dep(), dirty(), effect() (+24 more)

### Community 13 - "Django Database Models"
Cohesion: 0.17
Nodes (17): Area, Assay, AssaysPsi, Calendar, CorrectiveTask, Equipment, Estado, Meta (+9 more)

### Community 14 - "Assays Management View"
Cohesion: 0.11
Nodes (26): assaysData, colKeys, columnsConfig, currentFilters, currentPage, currentSort, equipmentsList, filterData (+18 more)

### Community 15 - "Corrective Tasks View"
Cohesion: 0.10
Nodes (25): colKeys, columnsConfig, currentFilters, currentPage, currentSort, { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams }, extractData(), filterData (+17 more)

### Community 16 - "Sampling Management View"
Cohesion: 0.09
Nodes (24): assays, colKeys, columnsConfig, equipmentOptions, filteredAssays, gridData, handleDelete(), handleSave() (+16 more)

### Community 17 - "Status Tasks View"
Cohesion: 0.10
Nodes (26): colKeys, currentFilters, currentPage, currentSort, error, estadosList, extractData(), filterData (+18 more)

### Community 18 - "General Tasks View"
Cohesion: 0.11
Nodes (23): colKeys, columnsConfig, currentFilters, currentPage, currentSort, { equipmentsList, loadDependencies, getEquipmentHierarchyRow, buildFilterParams }, extractData(), filterData (+15 more)

### Community 19 - "Weekly Dashboard View"
Cohesion: 0.09
Nodes (22): cargarDatos(), chartDataReady, chartDays, chartDaysShort, chartPersonnel, chartStats, currentYear, dashboardConfig (+14 more)

### Community 20 - "Vue Scheduler and Formatting"
Cohesion: 0.10
Nodes (28): checkRecursiveUpdates(), findInsertionIndex(), flushJobs(), flushPostFlushCbs(), flushPreFlushCbs(), formatComponentName(), formatProp(), formatProps() (+20 more)

### Community 21 - "Pinia and Reactivity Composition"
Cohesion: 0.17
Nodes (25): computed(), createRef(), effectScope(), isReactive(), isRef2(), markRaw(), propertyToRef(), ref() (+17 more)

### Community 22 - "Devtools Component Inspection"
Cohesion: 0.14
Nodes (25): addInspector(), addTimelineLayer(), cancelInspectComponentHighLighter(), create(), createDevToolsCtxHooks(), createHooks(), getAppRecord(), getCardElement() (+17 more)

### Community 23 - "Group Schedule View"
Cohesion: 0.09
Nodes (17): useApi(), allUniqueDates, allUsers, columnsConfig, dateRangeText, dateToWeekMap, gridColumns, gridData (+9 more)

### Community 24 - "Equipments Management View"
Cohesion: 0.13
Nodes (22): areasList, columnsConfig, currentFilters, currentPage, currentSort, equipmentsData, error, filterData (+14 more)

### Community 25 - "Areas Management View"
Cohesion: 0.14
Nodes (21): areasData, columnsConfig, currentFilters, currentPage, currentSort, error, filterData, handleDelete() (+13 more)

### Community 26 - "Users Management View"
Cohesion: 0.13
Nodes (21): colKeys, columnsConfig, currentFilters, currentPage, currentSort, filterData, gridData, handleDelete() (+13 more)

### Community 27 - "Pinia Devtools Integration"
Cohesion: 0.16
Nodes (22): actionGlobalCopyState(), actionGlobalOpenStateFile(), actionGlobalPasteState(), actionGlobalSaveState(), addStoreToDevtools(), addTimelineEvent(), checkClipboardAccess(), checkNotFocusedError() (+14 more)

### Community 28 - "Monthly Calendar View"
Cohesion: 0.11
Nodes (17): currentMonth, currentYear, dashboardConfig, daysInMonth, diasSemana, fetchMonthData(), getExtendedWeek(), gridData (+9 more)

### Community 29 - "Samples Management View"
Cohesion: 0.13
Nodes (20): columnsConfig, currentFilters, currentPage, currentSort, equipmentsList, filterData, handleDelete(), handleFilterChange() (+12 more)

### Community 30 - "Plants Management View"
Cohesion: 0.16
Nodes (19): currentFilters, currentPage, currentSort, error, filterData, handleDelete(), handleFilterChange(), handlePageChange() (+11 more)

### Community 31 - "Systems Management View"
Cohesion: 0.16
Nodes (19): currentFilters, currentPage, currentSort, error, filterData, handleDelete(), handleFilterChange(), handlePageChange() (+11 more)

### Community 32 - "User Permissions View"
Cohesion: 0.14
Nodes (19): colKeys, currentFilters, currentPage, currentSort, filterData, gridData, handleDelete(), handleFilterChange() (+11 more)

### Community 33 - "Vue Hook Management"
Cohesion: 0.11
Nodes (20): addHooks(), _applyPromised(), componentAdded(), componentEmit(), componentRemoved(), componentUpdated(), debounce(), deprecateHook() (+12 more)

### Community 34 - "Vue Reactivity Core"
Cohesion: 0.14
Nodes (17): applyTranslation(), createReactiveObject(), createRecord(), get(), getTargetType(), isClassComponent(), isMapEqual(), markAttrsAccessed() (+9 more)

### Community 35 - "Devtools Plugin Registry"
Cohesion: 0.12
Nodes (19): callEachWith(), callHook(), callHookParallel(), callHookWith(), find(), findApplicable(), getActiveInspectors(), getInspector() (+11 more)

### Community 36 - "Vue Router Utilities"
Cohesion: 0.12
Nodes (18): provide(), toValue(), unref(), watchEffect(), extractChangingRecords(), getOriginalPath(), includesParams(), isEquivalentArray() (+10 more)

### Community 37 - "Vue Reactivity Utilities"
Cohesion: 0.12
Nodes (24): checkIdentityKeys(), createInstrumentationGetter(), createInstrumentations(), createIterableMethod(), createReadonlyMethod(), hasPropsChanged(), initProps(), isEmitListener() (+16 more)

### Community 38 - "Pinia HMR and Devtools"
Cohesion: 0.15
Nodes (14): acceptHMRUpdate(), addIdentity(), callDevToolsPluginSetupFn(), clear(), disposePinia(), get(), getComponentInstance(), has() (+6 more)

### Community 39 - "Vue Router Guard Logic"
Cohesion: 0.18
Nodes (14): canOnlyBeCalledOnce(), checkChildMissingNameWithEmptyPath(), checkMissingParamsInAbsolutePath(), checkSameParams(), createRouterError(), extractComponentsGuards(), getElementPosition(), guardToPromiseFn() (+6 more)

### Community 40 - "Vue DOM Utilities"
Cohesion: 0.07
Nodes (41): addEventListener(), addTransitionClass(), callPendingCbs(), cloneIfMounted(), cloneVNode(), concat(), createInvoker(), deepCloneVNode() (+33 more)

### Community 41 - "Weekly Tasks Component"
Cohesion: 0.18
Nodes (8): cargarDatos(), cargarSemanaMasReciente(), diasSemana, fechasOrd, isemana, nsemana, rsemana, tareasAgrupadas

### Community 42 - "Data Serialization Utilities"
Cohesion: 0.20
Nodes (12): applyReferentialEqualityAnnotations(), applyValueAnnotations(), deserialize(), forEach(), generateReferentialEqualityAnnotations(), "../../node_modules/.pnpm/speakingurl@14.0.1/node_modules/speakingurl/lib/speakingurl.js"(), parse(), serialize() (+4 more)

### Community 43 - "Project Dependencies"
Cohesion: 0.18
Nodes (11): axios, date-fns, dependencies, axios, date-fns, pinia, vue, vue-router (+3 more)

### Community 44 - "Equipment Hierarchy API"
Cohesion: 0.22
Nodes (7): api, useEquipmentHierarchies(), diasSemana, fechasOrd, semana, tareasAgrupadas, values()

### Community 45 - "Devtools Setup Utilities"
Cohesion: 0.20
Nodes (11): addDevtools(), formatDisplay(), formatRouteLocation(), formatRouteRecordMatcherForStateInspector(), getDevtoolsGlobalHook(), getTarget(), isPerformanceSupported(), modifierForKey() (+3 more)

### Community 46 - "Grid Interaction Handlers"
Cohesion: 0.22
Nodes (10): applyFilter(), changePage(), changePageSize(), closeFilterMenu(), deleteSelectedRows(), emit, executeSave(), handleGlobalClick() (+2 more)

### Community 47 - "Vue Router Composition API"
Cohesion: 0.24
Nodes (10): inject(), injectToKeepAliveRoot(), onActivated(), onDeactivated(), registerKeepAliveHook(), onBeforeRouteLeave(), onBeforeRouteUpdate(), registerGuard() (+2 more)

### Community 48 - "Frontend Package Configuration"
Cohesion: 0.22
Nodes (8): name, private, scripts, build, dev, preview, type, version

### Community 49 - "Grid Formatting Utilities"
Cohesion: 0.33
Nodes (9): calculateAutoWidths(), fallbackCopy(), getCellValueStr(), getColumnOptions(), getFilterLabel(), getOptionLabel(), handleCopy(), handlePaste() (+1 more)

### Community 51 - "Router Instance Logic"
Cohesion: 0.28
Nodes (9): disconnectedCallback(), nextTick(), resolve(), getRoutes(), constructor(), createRouter(), createRouterMatcher(), mergeOptions() (+1 more)

### Community 54 - "Vue Router History"
Cohesion: 0.29
Nodes (8): createCurrentLocation(), createMemoryHistory(), createWebHashHistory(), createWebHistory(), normalizeBase(), stripBase(), useHistoryListeners(), useHistoryStateNavigation()

### Community 56 - "Object Utility Functions"
Cohesion: 0.33
Nodes (7): assignProp(), copy(), getType2(), isArray2(), isNull2(), isPlainObject3(), isUndefined2()

### Community 57 - "URL Query Encoding"
Cohesion: 0.33
Nodes (7): commonEncode(), encodeHash(), encodeParam(), encodePath(), encodeQueryKey(), encodeQueryValue(), stringifyQuery()

### Community 59 - "Router Path Matching"
Cohesion: 0.40
Nodes (6): comparePathParserScore(), compareScoreArray(), findInsertionIndex(), getInsertionAncestor(), isLastScoreNegative(), isMatchable()

### Community 60 - "Vite Build Dependencies"
Cohesion: 0.40
Nodes (5): devDependencies, vite, @vitejs/plugin-vue, vite, @vitejs/plugin-vue

### Community 61 - "Grid Data Helpers"
Cohesion: 0.60
Nodes (4): buildPayloadFromRow(), mapGridKeyToPayload(), numericKeys, sanitizeValue()

### Community 62 - "URL Parsing Utilities"
Cohesion: 0.40
Nodes (5): decode(), isRouteMatching(), parseQuery(), parseURL(), resolveRelativePath()

### Community 66 - "Task Database Entities"
Cohesion: 0.67
Nodes (4): CorrectiveTask, Task, TaskCatalog, TaskP

### Community 67 - "Excel Export Utility"
Cohesion: 0.50
Nodes (4): xlsx, exportToExcel(), exportToExcel(), xlsx

### Community 73 - "Grid Cell Navigation"
Cohesion: 0.67
Nodes (3): focusCell(), handleKeydown(), setActive()

### Community 74 - "Grid Resize Logic"
Cohesion: 0.67
Nodes (3): handleResizeMove(), initGrid(), stopResize()

## Knowledge Gaps
- **292 isolated node(s):** `Migration`, `Migration`, `Migration`, `Migration`, `Migration` (+287 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `values()` connect `Equipment Hierarchy API` to `User Permissions View`, `Vue Component Hooks`, `Vue DOM Utilities`, `Vue Devtools Internals`, `Assays Management View`, `Status Tasks View`, `Users Management View`?**
  _High betweenness centrality (0.277) - this node is a cross-community bridge._
- **Why does `useEquipmentHierarchies()` connect `Equipment Hierarchy API` to `General Tasks View`, `Corrective Tasks View`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Why does `value()` connect `Vue Component Hooks` to `Pinia Store Lifecycle`, `Vue Reactivity Utilities`, `Vue Custom Elements`, `Vue Devtools Internals`, `Data Serialization Utilities`, `Vue Reactivity Engine`, `Router Instance Logic`, `Pinia and Reactivity Composition`, `Monthly Calendar View`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `push()` (e.g. with `createRouter()` and `useHistoryStateNavigation()`) actually correct?**
  _`push()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `setup()` (e.g. with `applyTranslation()` and `callPendingCbs()`) actually correct?**
  _`setup()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Migration`, `Migration`, `Migration` to the rest of the system?**
  _292 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Pinia Store Lifecycle` be split into smaller, more focused modules?**
  _Cohesion score 0.0363963963963964 - nodes in this community are weakly interconnected._