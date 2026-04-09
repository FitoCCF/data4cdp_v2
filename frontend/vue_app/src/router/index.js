import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/plants',
            name: 'Plants',
            component: () => import('../views/genericViews/PlantsView.vue')
        },
        {
            path: '/areas',
            name: 'Areas',
            component: () => import('../views/genericViews/AreasView.vue')
        },
        {
            path: '/sistems',
            name: 'Systems',
            component: () => import('../views/genericViews/SystemsView.vue')
        },
        {
            path: '/equipments',
            name: 'Equipments',
            component: () => import('../views/genericViews/EquipmentsView.vue')
        },
        {
            path: '/samples',
            name: 'Samples',
            component: () => import('../views/genericViews/SamplesView.vue')
        },
        {
            path: '/assays',
            name: 'Assays',
            component: () => import('../views/genericViews/AssaysView.vue')
        },
        {
            path: '/tasks',
            name: 'Task',
            component: () => import('../views/genericViews/TasksView.vue')
        },
        {
            path: '/stasks',
            name: 'ScheduledTasks',
            component: () => import('../views/genericViews/STasksViews.vue')
        },
        /*
        {
            path: '/ctasks',
            name: 'CorrectiveTasks',
            component: () => import('../views/genericViews/CTasksView.vue')
        },
        */
        {
            path: '/weeklytasks',
            name: 'WeeklyTasks',
            component: () => import('../views/genericViews/WeeklyTasksView.vue')
        },
        {
            path: '/sampling',
            name: 'Sampling',
            component: () => import('../views/genericViews/SamplingView.vue')
        },
        {
            path: '/excel-test',
            name: 'ExcelTest',
            component: () => import('../views/ExcelTestView.vue')
        },
        // Dentro de tu array 'routes':
        {
            path: '/calendario-grupos',
            name: 'GroupSchedule',
            component: () => import('../views/genericViews/GroupScheduleView.vue')

        }

    ]
})

export default router
