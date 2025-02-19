import matplotlib.pyplot as plt
import float_to_posit as ftp
import posit_to_float as ptf
import numpy as np


def comp_trunc16(int_val, es):
    """
    Truncate a 16-bit Posit to 8-bit and compute percent error.
    """
    pos_16b = ftp.get_posit(int_val, es, 16)
    pos_8b = pos_16b[:8]  # Take the first 8 bits

    dec_8b = ptf.convert_posit(pos_8b, es)
    dec_16b = ptf.convert_posit(pos_16b, es)
    
    percent_error = abs((dec_8b - int_val) / int_val)
    
    return percent_error


def comp_16_8(int_val, es):
    """
    Directly compare 8-bit Posit and 16-bit Posit representations.
    """
    pos_8b = ftp.get_posit(int_val, es, 8)
    pos_16b = ftp.get_posit(int_val, es, 16)
    
    dec_8b = ptf.convert_posit(pos_8b, es)
    dec_16b = ptf.convert_posit(pos_16b, es)
    
    percent_error = abs((dec_8b - int_val) / int_val)
    
    return percent_error


def plot_two_percent_errors(x_values, trunc_errors, comp_errors, tolerance_percent=1.0):
    """
    Creates a figure with two subplots:
    - First subplot: Error from truncating a 16-bit Posit to 8-bit.
    - Second subplot: Error from directly comparing 8-bit and 16-bit Posits.
    
    Parameters:
    -----------
    x_values : list or array-like
        The x-values for which you have computed errors.
    trunc_errors : list or array-like
        Percent errors for the truncation method.
    comp_errors : list or array-like
        Percent errors for the direct comparison method.
    tolerance_percent : float, optional
        Any point with an absolute percent error <= tolerance_percent is considered 'within tolerance'.
        Default is 1.0 (i.e., 1%).
    """

    fig, axs = plt.subplots(2, 1, figsize=(8, 10), sharex=True)

    # --- First Subplot: Truncation Error ---
    within_tol_trunc = [abs(err) <= tolerance_percent for err in trunc_errors]
    axs[0].scatter(x_values, trunc_errors, color='blue', s=10, label='All Points')
    axs[0].scatter(
        np.array(x_values)[within_tol_trunc], np.array(trunc_errors)[within_tol_trunc],
        color='green', s=10, label='Within Tolerance'
    )
    axs[0].scatter(
        np.array(x_values)[~np.array(within_tol_trunc)], np.array(trunc_errors)[~np.array(within_tol_trunc)],
        color='red', s=10, label='Out of Tolerance'
    )
    axs[0].set_ylabel('Percent Error (%)')
    axs[0].set_title('Truncate 16-bit Posit → 8-bit')
    axs[0].legend()
    axs[0].grid(True)

    # --- Second Subplot: Direct 8-bit vs. 16-bit Comparison ---
    within_tol_comp = [abs(err) <= tolerance_percent for err in comp_errors]
    axs[1].scatter(x_values, comp_errors, color='blue', s=10, label='All Points')
    axs[1].scatter(
        np.array(x_values)[within_tol_comp], np.array(comp_errors)[within_tol_comp],
        color='green', s=10, label='Within Tolerance'
    )
    axs[1].scatter(
        np.array(x_values)[~np.array(within_tol_comp)], np.array(comp_errors)[~np.array(within_tol_comp)],
        color='red', s=10, label='Out of Tolerance'
    )
    axs[1].set_xlabel('x')
    axs[1].set_ylabel('Percent Error (%)')
    axs[1].set_title('Compare 8-bit Posit vs. 16-bit Posit')
    axs[1].legend()
    axs[1].grid(True)

    # Save and Show
    plt.savefig("Relative_Error_TruncVsRep.png", dpi=300, bbox_inches='tight')
    plt.show()


# Run the error comparison and plot
es = 1
tolerance = 0.1
xvals = list(range(1, 300))

# Compute errors
trunc_errors = [comp_trunc16(n, es) for n in xvals]
comp_errors = [comp_16_8(n, es) for n in xvals]

# Plot both comparisons
plot_two_percent_errors(xvals, trunc_errors, comp_errors, tolerance)
