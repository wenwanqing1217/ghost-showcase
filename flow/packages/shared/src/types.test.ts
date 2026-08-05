import { describe, it, expect } from 'vitest'
import { WorkflowTemplate, WorkflowExecutionResult, ExecutionStep, Workflow, WorkflowNode } from '../src/types'

describe('Workflow Types', () => {
  it('should define a valid workflow template', () => {
    const template: WorkflowTemplate = {
      id: 'test-template',
      name: 'Test Template',
      description: 'A test workflow template',
      trigger: {
        type: 'keyword',
        patterns: ['test', 'keyword'],
      },
      workflow: {
        id: 'test-workflow',
        name: 'Test Workflow',
        description: 'A test workflow',
        nodes: [
          { id: 'node1', type: 'search', name: 'Search Node' },
        ],
        edges: [{ from: 'node1', to: 'node2' }],
      },
    }

    expect(template.id).toBe('test-template')
    expect(template.trigger.patterns).toContain('test')
    expect(template.workflow.nodes).toHaveLength(1)
  })

  it('should define a valid execution step', () => {
    const step: ExecutionStep = {
      nodeId: 'node1',
      nodeName: 'Test Node',
      status: 'success',
      output: { result: 'test' },
      duration: 100,
    }

    expect(step.status).toBe('success')
    expect(step.output).toEqual({ result: 'test' })
    expect(step.duration).toBe(100)
  })

  it('should define a valid execution result', () => {
    const result: WorkflowExecutionResult = {
      success: true,
      workflowId: 'workflow-1',
      workflowName: 'Test Workflow',
      result: 'Success',
      steps: [],
    }

    expect(result.success).toBe(true)
    expect(result.error).toBeUndefined()
  })

  it('should support error state in execution result', () => {
    const result: WorkflowExecutionResult = {
      success: false,
      workflowId: 'workflow-1',
      workflowName: 'Test Workflow',
      result: 'Failed',
      steps: [],
      error: 'Something went wrong',
    }

    expect(result.success).toBe(false)
    expect(result.error).toBe('Something went wrong')
  })
})
