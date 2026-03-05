import { createRouter, createWebHistory } from 'vue-router'
import { defineAsyncComponent } from 'vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/plants',
            name: 'Plants',
            component: defineAsyncComponent(() => import('../views/genericViews/PlantsView.vue'))
        },
        {
            path: '/areas',
            name: 'Areas',
            component: defineAsyncComponent(() => import('../views/genericViews/AreasView.vue'))
        },
        {
            path: '/sistems',
            name: 'Systems',
            component: defineAsyncComponent(() => import('../views/genericViews/SystemsView.vue'))
        },
        {
            path: '/equipments',
            name: 'Equipments',
            component: defineAsyncComponent(() => import('../views/genericViews/EquipmentsView.vue'))
        },
        {
            path: '/samples',
            name: 'Samples',
            component: defineAsyncComponent(() => import('../views/genericViews/SamplesView.vue'))
        },
        {
            path: '/assays',
            name: 'Assays',
            component: defineAsyncComponent(() => import('../views/genericViews/AssaysView.vue'))
        },
        {
            path: '/tasks',
            name: 'Task',
            component: defineAsyncComponent(() => import('../views/genericViews/TasksView.vue'))
        },
        {
            path: '/stasks',
            name: 'ScheduledTasks',
            component: defineAsyncComponent(() => import('../views/genericViews/STasksViews.vue'))
        },
        /*
        {
            path: '/ctasks',
            name: 'CorrectiveTasks',
            component: defineAsyncComponent(() => import('../views/genericViews/CTasksView.vue'))
        },
        */
        {
            path: '/weeklytasks',
            name: 'WeeklyTasks',
            component: defineAsyncComponent(() => import('../views/genericViews/WeeklyTasksView.vue'))
        },
        {
            path: '/sampling',
            name: 'Sampling',
            component: defineAsyncComponent(() => import('../views/genericViews/SamplingView.vue'))
        },
        {
            path: '/excel-test',
            name: 'ExcelTest',
            component: defineAsyncComponent(() => import('../views/ExcelTestView.vue'))
        }

    ]
})

export default router
