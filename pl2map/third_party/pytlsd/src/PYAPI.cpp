#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <iostream>
#include "lsd.h"

#define STRINGIFY(x) #x
#define MACRO_STRINGIFY(x) STRINGIFY(x)
namespace py = pybind11;

void check_img_format(const py::buffer_info& correct_info, const py::buffer_info& info, std::string name=""){
  std::stringstream ss;
  if (info.format != correct_info.format) {
    ss << "Error: " << name << " array has format \"" << info.format
       << "\" but the format should be \"" << correct_info.format << "\"";
    throw py::type_error(ss.str());
  }
  if (info.shape.size() != correct_info.shape.size()) {
    ss << "Error: " << name << " array has " << info.shape.size()
       << "dimensions but should have " << correct_info.shape.size();
    throw py::type_error(ss.str());
  }

  for(int i =0 ; i < info.shape.size() ; i++){
    if (info.shape[i] != correct_info.shape[i]) {
      ss << "Error: " << name << " array has " << info.shape[i] << " elements in dimension " << info.shape.size()
         << " but should have " << correct_info.shape[i];
      throw py::type_error(ss.str());
    }
  }
}

struct LineSegment
{
  double x1, y1, x2, y2, /*width, */ p /*, new_log10_NFA*/;
};

// Passing in a generic array
// Passing in an array of doubles
py::array_t<float> run_lsd(const py::array_t<double>& img,
                           double scale=0.8,
                           double sigma_scale=0.6,
                           double density_th=0.0, /* Minimal density of region points in rectangle. */
                           const py::array_t<double>& gradnorm = py::array_t<double>(),
                           const py::array_t<double>& gradangle = py::array_t<double>(),
                           bool grad_nfa = false) {
  double quant = 2.0;       /* Bound to the quantization error on the
                                gradient norm.                                */
  double ang_th = 22.5;     /* Gradient angle tolerance in degrees.           */
  // double log_eps = 0.0;     /* Detection threshold: -log10(NFA) > log_eps     */
  int n_bins = 1024;        /* Number of bins in pseudo-ordering of gradient
                               modulus.                                       */
  double log_eps = 0;

  py::buffer_info info = img.request();
  if (info.format != "d" && info.format != "B" ) {
    throw py::type_error("Error: The provided numpy array has the wrong type");
  }

  double *modgrad_ptr{};
  double *angles_ptr{};
  if (gradnorm.size() != 0 ) {
    py::buffer_info gradnorm_info = gradnorm.request();
    check_img_format(info, gradnorm_info, "Gradnorm");
    modgrad_ptr = static_cast<double *>(gradnorm_info.ptr);
  }

  if (gradangle.size() != 0) {
    py::buffer_info gradangle_info = gradangle.request();
    check_img_format(info, gradangle_info, "Gradangle");
    angles_ptr = static_cast<double *>(gradangle_info.ptr);
  }

  if (info.shape.size() != 2) {
    throw py::type_error("Error: You should provide a 2 dimensional array.");
  }

  double *imagePtr = static_cast<double *>(info.ptr);

  // LSD call. Returns [x1,y1,x2,y2,width,p,-log10(NFA)] for each segment
  int N;
  double *out = LineSegmentDetection(
    &N, imagePtr, info.shape[1], info.shape[0], scale, sigma_scale, quant,
    ang_th, log_eps, density_th, n_bins, grad_nfa, modgrad_ptr, angles_ptr);

  py::array_t<float> segments({N, 5});
  for (int i = 0; i < N; i++) {
    segments[py::make_tuple(i, 0)] = out[7 * i + 0];
    segments[py::make_tuple(i, 1)] = out[7 * i + 1];
    segments[py::make_tuple(i, 2)] = out[7 * i + 2];
    segments[py::make_tuple(i, 3)] = out[7 * i + 3];
    segments[py::make_tuple(i, 4)] = out[7 * i + 5];
    // p:           out[7 * i + 4]);
    // -log10(NFA): out[7 * i + 5]);
  }
  free((void *) out);
  return segments;
}

py::list batched_run_lsd(const py::array_t<double>& img,
                                   double scale=0.8,
                                   double sigma_scale=0.6,
                                   double density_th=0.0, /* Minimal density of region points in rectangle. */
                                   const py::array_t<double>& gradnorm = py::array_t<double>(),
                                   const py::array_t<double>& gradangle = py::array_t<double>(),
                                   bool grad_nfa = false) {
  double quant = 2.0;       /* Bound to the quantization error on the
                                gradient norm.                                */
  double ang_th = 22.5;     /* Gradient angle tolerance in degrees.           */
  // double log_eps = 0.0;     /* Detection threshold: -log10(NFA) > log_eps     */
  int n_bins = 1024;        /* Number of bins in pseudo-ordering of gradient
                               modulus.                                       */
  double log_eps = 0;

  py::buffer_info info = img.request();
  if (info.format != "d" && info.format != "B" ) {
    throw py::type_error("Error: The provided numpy array has the wrong type");
  }

  double *modgrad_ptr{};
  double *angles_ptr{};
  if (gradnorm.size() != 0 ) {
    py::buffer_info gradnorm_info = gradnorm.request();
    check_img_format(info, gradnorm_info, "Gradnorm");
    modgrad_ptr = static_cast<double *>(gradnorm_info.ptr);
  }

  if (gradangle.size() != 0) {
    py::buffer_info gradangle_info = gradangle.request();
    check_img_format(info, gradangle_info, "Gradangle");
    angles_ptr = static_cast<double *>(gradangle_info.ptr);
  }

  if (info.shape.size() != 3) {
    throw py::type_error("Error: You should provide a 3 dimensional array (batch, height, width)");
  }

  double *imagePtr = static_cast<double *>(info.ptr);

  const size_t batch_size = info.shape[0];
  const size_t img_size = info.shape[2] * info.shape[1];

  std::vector<std::shared_ptr<std::vector<LineSegment>>> tmp(batch_size);

  #pragma omp parallel for
  for (int b = 0 ; b < batch_size ; b++){
    // LSD call. Returns [x1,y1,x2,y2,width,p,-log10(NFA)] for each segment
    int N;
    double *out = LineSegmentDetection(
      &N, imagePtr + b * img_size, info.shape[2], info.shape[1], scale, sigma_scale, quant,
      ang_th, log_eps, density_th, n_bins, grad_nfa, modgrad_ptr, angles_ptr);

    tmp[b] = std::make_shared< std::vector<LineSegment> >(N);
    LineSegment * p_data = tmp[b]->data();
    for (int i = 0; i < N; i++) {
      p_data->x1 = out[7 * i + 0];
      p_data->y1 = out[7 * i + 1];
      p_data->x2 = out[7 * i + 2];
      p_data->y2 = out[7 * i + 3];
      p_data->p = out[7 * i + 5];
      p_data++;
    }
    free(out);
  }

  py::list segments;
  for (int b = 0; b < batch_size; b++){
    py::array_t<float> tmp2({int(tmp[b]->size()), 5});
    for (int i = 0; i < tmp[b]->size(); i++){
      tmp2[py::make_tuple(i, 0)] = tmp[b]->at(i).x1;
      tmp2[py::make_tuple(i, 1)] = tmp[b]->at(i).y1;
      tmp2[py::make_tuple(i, 2)] = tmp[b]->at(i).x2;
      tmp2[py::make_tuple(i, 3)] = tmp[b]->at(i).y2;
      tmp2[py::make_tuple(i, 4)] = tmp[b]->at(i).p;
    }
    segments.append(tmp2);

  }

  return segments;
}


PYBIND11_MODULE(pytlsd, m) {
    m.doc() = R"pbdoc(
        Python transparent bindings for LSD (Line Segment Detector)
        -----------------------

        .. currentmodule:: pytlsd

        .. autosummary::
           :toctree: _generate

           lsd
    )pbdoc";

    m.def("lsd", &run_lsd, R"pbdoc(
        Computes Line Segment Detection (LSD) in the image.
    )pbdoc",
          py::arg("img"),
          py::arg("scale") = 0.8,
          py::arg("sigma_scale") = 0.6,
          py::arg("density_th") = 0.0,
          py::arg("gradnorm") = py::array(),
          py::arg("gradangle") = py::array(),
          py::arg("grad_nfa") = false);

  m.def("batched_lsd", &batched_run_lsd, R"pbdoc(
        Computes Line Segment Detection (LSD) in the image.
    )pbdoc",
      py::arg("img"),
      py::arg("scale") = 0.8,
      py::arg("sigma_scale") = 0.6,
      py::arg("density_th") = 0.0,
      py::arg("gradnorm") = py::array(),
      py::arg("gradangle") = py::array(),
      py::arg("grad_nfa") = false);

#ifndef _MSC_VER
#ifdef VERSION_INFO
    m.attr("__version__") = MACRO_STRINGIFY(VERSION_INFO);
#else
    m.attr("__version__") = "dev";
#endif
#endif
}
