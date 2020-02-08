import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
from decimal import Decimal
from slicer.util import VTKObservationMixin

#
# FiducialToModelDistance
#

class FiducialToModelDistance(ScriptedLoadableModule):

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Fiducial to Model Distance"
    self.parent.categories = ["Quantification"]
    self.parent.dependencies = []
    self.parent.contributors = ["Jesse Reynolds (Canterbury District Health Board) with assistance from Andras Lasso (Queen's University), "] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module computes the distances between a set of fiducial points and either the surface of a model, or another set of fiducial points. The results are displayed in two tables.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jesse Reynolds (Canterbury District Health Board) with assistance from Andras Lasso (Queen's University)."""

#
# FiducialToModelDistanceWidget
#

class FiducialToModelDistanceWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)
    self.logic = None
    self._parameterNode = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)
    
    # Create a new parameterNode
    self.logic = FiducialToModelDistanceLogic()
        
    # Load rest of the widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/FiducialToModelDistance.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)
    uiWidget.setMRMLScene(slicer.mrmlScene)
    self.setParameterNode(self.logic.getParameterNode())

    self.ui.parameterNodeSelector.addAttribute( "vtkMRMLScriptedModuleNode", "ModuleName", "FiducialToModelDistance" )
        
    # Connections to update parameter node when GUI is changed
    self.ui.parameterNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setParameterNode)
    self.ui.inputPointsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.inputReferenceNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputMetricsTableNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.outputDistancesTableNodeSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

    # Connections to button clicks
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.showMetricsTablePushButton.connect('clicked(bool)', self.onShowMetricsTableButton)
    self.ui.showDistancesTablePushButton.connect('clicked(bool)', self.onShowDistancesTableButton)

    # Add vertical spacer
    self.layout.addStretch(1)
    
    # Update GUI From Parameter Node
    self.updateGUIFromParameterNode()

  def cleanup(self):
    self.removeObservers()

  def setParameterNode(self, inputParameterNode):
    if inputParameterNode == self._parameterNode:
      return
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    if inputParameterNode is not None:
      self.addObserver(inputParameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode
    self.updateGUIFromParameterNode()
         
  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    Query all the parameters in the parameterNode,
    and update the GUI state accordingly if something has changed.
    """
    
    self.ui.inputsOutputsCollapsibleButton.enabled = self._parameterNode is not None
    if self._parameterNode is None:
      return

    wasBlocked = self.ui.inputPointsSelector.blockSignals(True)
    self.ui.inputPointsSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputPoints"))
    self.ui.inputPointsSelector.blockSignals(wasBlocked) 

    wasBlocked = self.ui.inputReferenceNodeSelector.blockSignals(True)
    self.ui.inputReferenceNodeSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputReference"))
    self.ui.inputReferenceNodeSelector.blockSignals(wasBlocked) 

    wasBlocked = self.ui.outputMetricsTableNodeSelector.blockSignals(True)
    self.ui.outputMetricsTableNodeSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputMetrics"))
    self.ui.outputMetricsTableNodeSelector.blockSignals(wasBlocked) 
    self.ui.showMetricsTablePushButton.enabled = self._parameterNode.GetNodeReference("OutputMetrics") is not None

    wasBlocked = self.ui.outputDistancesTableNodeSelector.blockSignals(True)
    self.ui.outputDistancesTableNodeSelector.setCurrentNode(self._parameterNode.GetNodeReference("OutputDistances"))
    self.ui.outputDistancesTableNodeSelector.blockSignals(wasBlocked) 
    self.ui.showDistancesTablePushButton.enabled = self._parameterNode.GetNodeReference("OutputDistances") is not None

    if self._parameterNode.GetNodeReference("OutputMetrics") or self._parameterNode.GetNodeReference("OutputDistances"):
      self.ui.applyButton.toolTip = "Compute results and write to output tables"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select output metrics or distances table"
      self.ui.applyButton.enabled = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    Query all the parameters in the parameterNode,
    and update the GUI state accordingly if something has changed.
    """
    
    if self._parameterNode is None:
      return

    self._parameterNode.SetNodeReferenceID("InputPoints", self.ui.inputPointsSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("InputReference", self.ui.inputReferenceNodeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputMetrics", self.ui.outputMetricsTableNodeSelector.currentNodeID)
    self._parameterNode.SetNodeReferenceID("OutputDistances", self.ui.outputDistancesTableNodeSelector.currentNodeID)

  def onApplyButton(self):
    logic = FiducialToModelDistanceLogic()
    try:
      logic.compute(self._parameterNode.GetNodeReference("InputPoints"), self._parameterNode.GetNodeReference("InputReference"),
        self._parameterNode.GetNodeReference("OutputMetrics"), self._parameterNode.GetNodeReference("OutputDistances"))
    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()
    
  @staticmethod
  def showTable(tableNodeID):
    currentLayout = slicer.app.layoutManager().layout
    layoutWithTable = slicer.modules.tables.logic().GetLayoutWithTable(currentLayout)
    slicer.app.layoutManager().setLayout(layoutWithTable)
    slicer.app.applicationLogic().GetSelectionNode().SetActiveTableID(tableNodeID)
    slicer.app.applicationLogic().PropagateTableSelection() 

  def onShowMetricsTableButton(self):
    FiducialToModelDistanceWidget.showTable(self._parameterNode.GetNodeReferenceID("OutputMetrics"))
    
  def onShowDistancesTableButton(self):
    FiducialToModelDistanceWidget.showTable(self._parameterNode.GetNodeReferenceID("OutputDistances"))


#
# FiducialToModelDistanceLogic
#

class FiducialToModelDistanceLogic(ScriptedLoadableModuleLogic):

  def pointDistancesLabelsFromPoints(self, inputPoints, referencePoints):
    """Calculate closest point to point distance"""
    if referencePoints.GetNumberOfControlPoints() == 0:
      raise ValueError("Empty reference points node")
    if inputPoints.GetNumberOfControlPoints() == 0:
      raise ValueError("Empty input points node")
    nOfMovingFiducialPoints = inputPoints.GetNumberOfFiducials()
    nOfFixedFiducialPoints = referencePoints.GetNumberOfFiducials()
    import numpy as np
    distances = np.zeros(nOfMovingFiducialPoints)
    labels = [""] * nOfMovingFiducialPoints
    for i in range(nOfMovingFiducialPoints):
      movingPointWorld = np.zeros(3)
      inputPoints.GetNthControlPointPositionWorld(i, movingPointWorld)
      for j in range(0, nOfFixedFiducialPoints):
        fixedPointWorld = np.zeros(3)
        referencePoints.GetNthControlPointPositionWorld(j, fixedPointWorld)
        dist = (vtk.vtkMath.Distance2BetweenPoints(movingPointWorld,fixedPointWorld)) ** 0.5
        if j == 0:
          minDist = dist
          closestLabel = referencePoints.GetNthControlPointLabel(j)
        elif minDist > dist:
          minDist = dist
          closestLabel = referencePoints.GetNthControlPointLabel(j)
      distances[i] = minDist
      labels[i] = inputPoints.GetNthControlPointLabel(i) + " to " + closestLabel

    return distances, labels

  def pointDistancesLabelsFromSurface(self, inputPoints, inputModel):
    """Calculate closest point to point distance"""
    if not inputModel.GetPolyData() or inputModel.GetPolyData().GetNumberOfPoints() == 0:
      raise ValueError("Empty input model")

    # Transform model polydata to world coordinate system
    if inputModel.GetParentTransformNode():
      transformModelToWorld = vtk.vtkGeneralTransform()
      slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(inputModel.GetParentTransformNode(), None, transformModelToWorld)
      polyTransformToWorld = vtk.vtkTransformPolyDataFilter()
      polyTransformToWorld.SetTransform(transformModelToWorld)
      polyTransformToWorld.SetInputData(inputModel.GetPolyData())
      polyTransformToWorld.Update()
      surface_World = polyTransformToWorld.GetOutput()
    else:
      surface_World = inputModel.GetPolyData()

    distanceFilter = vtk.vtkImplicitPolyDataDistance()
    distanceFilter.SetInput(surface_World)
    nOfFiducialPoints = inputPoints.GetNumberOfFiducials()
    import numpy as np
    distances = np.zeros(nOfFiducialPoints)
    labels = [""] * nOfFiducialPoints
    for i in range(nOfFiducialPoints):
      point_World = np.zeros(3)
      inputPoints.GetNthControlPointPositionWorld(i, point_World)
      closestPointOnSurface_World = np.zeros(3)
      closestPointDistance = distanceFilter.EvaluateFunctionAndGetClosestPoint(point_World, closestPointOnSurface_World)
      labels[i] = inputPoints.GetNthControlPointLabel(i)
      distances[i] = closestPointDistance

    return distances, labels

  def compute(self, inputPoints, inputReference, outputMetricsTable, outputDistancesTable):

    if inputReference.IsA("vtkMRMLMarkupsFiducialNode"):
      pointDistances, labels = self.pointDistancesLabelsFromPoints(inputPoints, inputReference)
    else:
      pointDistances, labels = self.pointDistancesLabelsFromSurface(inputPoints, inputReference)

    if outputDistancesTable:
      # Create arrays to store results
      indexCol = vtk.vtkIntArray()
      indexCol.SetName("Index")
      distanceCol = vtk.vtkDoubleArray()
      distanceCol.SetName("Distance")
      labelCol = vtk.vtkStringArray()
      labelCol.SetName("Description")
      for i in range(len(pointDistances)):
        indexCol.InsertNextValue(i)
        distanceCol.InsertNextValue(pointDistances[i])
        labelCol.InsertNextValue(labels[i])
      outputDistancesTable.RemoveAllColumns()
      outputDistancesTable.AddColumn(indexCol)
      outputDistancesTable.AddColumn(distanceCol)
      outputDistancesTable.AddColumn(labelCol)

    if outputMetricsTable:
      import numpy as np
      metricValues = []
      metricLabels = []

      metricLabels.append("Mean Distance")
      metricValues.append(pointDistances.mean())
      metricLabels.append("Root Mean Square Distance")
      metricValues.append(np.sqrt((pointDistances**2).mean()))
      metricLabels.append("Maximum Distance")
      metricValues.append(pointDistances.max())
      metricLabels.append("Minimum Distance")
      metricValues.append(pointDistances.min())

      if inputReference.IsA("vtkMRMLMarkupsFiducialNode"):
        # Hausdorff Distance is the max of the minimum distances
        inversePointDistances, inverseLabels = self.pointDistancesLabelsFromPoints(inputReference, inputPoints)
        metricLabels.append("Hausdorff Distance")
        metricValues.append(max(abs(pointDistances).min(), abs(inversePointDistances).min()))
      else:
        metricLabels.append("Mean Absolute Distance")
        metricValues.append(abs(pointDistances).mean())
        metricLabels.append("Maximum Absolute Distance")
        metricValues.append(abs(pointDistances).max())
        metricLabels.append("Minimum Absolute Distance")
        metricValues.append(abs(pointDistances).min())

      slicer.util.updateTableFromArray(outputMetricsTable, [np.array(v) for v in metricValues], metricLabels)
  

class FiducialToModelDistanceTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_FiducialToModelDistance1()

  def test_FiducialToModelDistance1(self):

    self.delayDisplay("Starting the test")
    
    # Create a 100 x 100 x 100mm cube
    cube = vtk.vtkCubeSource()
    cube.SetBounds(-50, 50, -50, 50, -50, 50)
    cube.Update()
    modelsLogic = slicer.modules.models.logic()
    modelsLogic.AddModel(cube.GetOutput())
    modelNode = slicer.util.getNode("Model")
    modelNode.GetDisplayNode().SetSliceIntersectionVisibility(1)
    
    # function for adding fiducial points
    def addFiducialPoints(title, fiducialPoints):
      fiducialNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode', title)
      point = vtk.vtkVector3d()
      for fiducialPoint in fiducialPoints:
        point.Set(fiducialPoint[0], fiducialPoint[1], fiducialPoint[2])
        fiducialNode.AddControlPointWorld(point)
      return fiducialNode
        
    # Add a set of moving fiducial points and a set of fixed fiducial points
    movingFiducialPoints = [[51.5, 0, 0], [-52.3, 0, 0], [0, 51.25, 0], [0, -52.1, 0], [0, 0, 51.7], [0, 0, -48.7]]
    fixedFiducialPoints = [[50, 0, 0], [-50, 0, 0], [0, 50, 0], [0, -50, 0], [0, 0, 50], [0, 0, -50]]
    
    movingFiducialNode = addFiducialPoints("Moving", movingFiducialPoints)
    movingFiducialNode.GetDisplayNode().SetSelectedColor(0,0,1)  # Change color of moving fiducial node to blue
    fixedFiducialNode = addFiducialPoints("Fixed", fixedFiducialPoints)
    
    # Some display settings
    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()

    logic = FiducialToModelDistanceLogic()
    metricsTable = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Metrics")
    distancesTable = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "Distances")

    # Run Fiducial to Model Distance
    logic.compute(movingFiducialNode, modelNode, metricsTable, distancesTable)
    checks = [
      ('Mean Distance', 1.25833),
      ('Root Mean Square Distance', 1.7365),
      ('Maximum Distance', 2.3),
      ('Minimum Distance', -1.3),
      ('Mean Absolute Distance', 1.69167),
      ('Maximum Absolute Distance', 2.3),
      ('Minimum Absolute Distance', 1.25)
    ]
    for metricName, metricValue in checks:
      self.assertAlmostEqual(metricsTable.GetTable().GetColumnByName(metricName).GetValue(0), metricValue, places=3, msg=metricName)
    self.delayDisplay('Fiducial to Model Distance Test Passed!')
    
    # Run Fiducial to Fiducial Distance
    logic.compute(movingFiducialNode, fixedFiducialNode, metricsTable, distancesTable)
    checks = [
      ('Mean Distance', 1.69167),
      ('Root Mean Square Distance', 1.7365),
      ('Maximum Distance', 2.3),
      ('Minimum Distance', 1.25),
      ('Hausdorff Distance', 1.25)
    ]
    for metricName, metricValue in checks:
      self.assertAlmostEqual(metricsTable.GetTable().GetColumnByName(metricName).GetValue(0), metricValue, places=3, msg=metricName)
    self.delayDisplay('Fiducial to Fiducial Distance Test Passed!')
        
    self.delayDisplay("All Tests Passed!")
    